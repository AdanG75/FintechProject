from typing import Union

from fastapi import APIRouter, Depends, Path, Query, Body, HTTPException
from pydantic import ValidationError
from redis.client import Redis
from sqlalchemy.orm import Session
from starlette import status
from starlette.background import BackgroundTasks

from controller.credit_controller import get_id_of_owners_of_credit
from controller.fingerprint_controller import set_minutiae_and_core_points_to_a_fingerprint, get_client_fingerprint, \
    validate_operation_by_fingerprints
from controller.general_controller import check_performer_in_cache, save_performer_in_cache, \
    get_type_auth_movement_cache, get_fingerprint_auth_data, add_attempt_cache, delete_performer_in_cache, \
    erase_attempt_cache
from controller.login_controller import get_current_token, get_logged_user_to_make_movement
from controller.movement_controller import get_payments_of_client, get_payments_of_market, create_summary_of_movement, \
    make_movement_based_on_type, finish_movement_unsuccessfully, save_movement_fingerprint, \
    save_type_authentication_in_cache, get_id_requester_from_movement, save_authentication_movement_result_in_cache
from controller.secure_controller import cipher_response_message, get_data_from_secure
from core.logs import show_error_message
from db.cache.cache import get_cache_client
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, type_of_value_not_compatible, \
    validation_request_exception, cache_exception, compile_exception, not_longer_available_exception, \
    type_of_authorization_not_compatible_exception
from schemas.basic_response import BasicResponse
from schemas.fingerprint_model import FingerprintB64
from schemas.movement_base import MovementTypeRequest
from schemas.movement_complex import MovementExtraRequest, BasicExtraMovement
from schemas.payment_base import PaymentComplexList
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary
from schemas.type_auth_movement import TypeAuthMovement, TypeAuthFrom
from schemas.type_movement import TypeMovement
from schemas.type_user import TypeUser

router = APIRouter(
    tags=['movement']
)


@router.post(
    path='/movement/summary',
    response_model=Union[SecureBase, MovementExtraRequest],
    status_code=status.HTTP_200_OK
)
async def get_movement_summary(
        request: Union[SecureBase, MovementTypeRequest] = Body(...),
        secure: bool = Query(True),
        type_movement: TypeMovement = Query(None),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    data_request = get_data_from_secure(request) if secure else request
    try:
        summary_request = MovementTypeRequest.parse_obj(data_request) \
            if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    if type_movement is None:
        type_movement = summary_request.type_movement

    if request.id_credit is not None:
        id_client, id_market = get_id_of_owners_of_credit(db, request.id_credit)
        id_requester = id_client
    else:
        id_requester = None

    data_user = get_logged_user_to_make_movement(current_token)
    data_user.id_requester = id_requester

    response = await create_summary_of_movement(db, summary_request, data_user, type_movement)
    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.post(
    path='/movement/type/{type_movement}',
    response_model=Union[SecureBase, BasicExtraMovement],
    status_code=status.HTTP_201_CREATED
)
async def make_movement(
        type_movement: TypeMovement = Path(...),
        request: Union[SecureBase, MovementExtraRequest] = Body(...),
        secure: bool = Query(False),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    data_request = get_data_from_secure(request) if secure else request
    try:
        movement_request = MovementExtraRequest.parse_obj(data_request) \
            if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    if type_movement != movement_request.type_movement:
        raise type_of_value_not_compatible

    if request.id_credit is not None:
        id_client, id_market = get_id_of_owners_of_credit(db, request.id_credit)
        id_requester = id_client
    else:
        id_requester = None

    data_user = get_logged_user_to_make_movement(current_token)
    data_user.id_requester = id_requester

    response = await make_movement_based_on_type(db, request, data_user, type_movement)

    # Save type_of authorization and performer if a response is created
    try:
        auth_type_result = await save_type_authentication_in_cache(
            r=r,
            id_movement=response.id_movement,
            type_movement=response.type_movement,
            type_sub_movement=response.extra.type_submov,
            performer_data=data_user
        )
        cache_result = await save_performer_in_cache(r, 'MOV', response.id_movement, current_token.id_user, 3600)
    except ValueError as ve:
        show_error_message(ve)
        finish_movement_unsuccessfully(db, id_movement=response.id_movement)
        raise compile_exception
    except Exception as e:
        show_error_message(e)
        finish_movement_unsuccessfully(db, id_movement=response.id_movement)
        raise compile_exception

    if not cache_result or not auth_type_result:
        finish_movement_unsuccessfully(db, id_movement=response.id_movement)
        raise cache_exception

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.post(
    path='/movement/{id_movement}/auth/fingerprint',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_202_ACCEPTED
)
async def save_fingerprint_to_authorize_movement(
        id_movement: int = Path(..., gt=0),
        request: Union[SecureBase, FingerprintB64] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    is_performer = check_performer_in_cache(r, id_movement, 'MOV', current_token.id_user)
    type_auth = get_type_auth_movement_cache(r, id_movement)

    if is_performer is False:
        raise not_authorized_exception

    if is_performer is None:
        finish_movement_unsuccessfully(db, id_movement=id_movement)
        raise not_longer_available_exception

    r_auth_type = await type_auth
    if not (r_auth_type == TypeAuthMovement.local.value or r_auth_type == TypeAuthMovement.localPaypal.value):
        raise type_of_authorization_not_compatible_exception

    data_request = get_data_from_secure(request) if secure else request
    try:
        fingerprint_request = FingerprintB64.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    result = await save_movement_fingerprint(r, id_movement, fingerprint_request)

    response = BasicResponse(
        operation="Save movement fingerprint",
        successful=result
    )
    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/movement/{id_movement}/auth/match',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_200_OK
)
async def authorize_movement_using_fingerprint(
        bt: BackgroundTasks,
        id_movement: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    is_performer = check_performer_in_cache(r, id_movement, 'MOV', current_token.id_user)
    type_auth = get_type_auth_movement_cache(r, id_movement)
    id_client = get_id_requester_from_movement(db, id_movement)

    if is_performer is False:
        raise not_authorized_exception

    if is_performer is None:
        finish_movement_unsuccessfully(db, id_movement=id_movement)
        raise not_longer_available_exception

    r_auth_type = await type_auth
    if not (r_auth_type == TypeAuthMovement.local.value or r_auth_type == TypeAuthMovement.localPaypal.value):
        raise type_of_authorization_not_compatible_exception

    # All movements which need to be authorized by the client's fingerprint require a requester
    r_id_client = await id_client
    if r_id_client is None:
        raise type_of_authorization_not_compatible_exception

    # Get minutiae and core points from cache
    minutiae, core_points = get_fingerprint_auth_data(r, 'MOV', id_movement)

    # Generate fingerprint object using minutiae and core points
    auth_fingerprint = set_minutiae_and_core_points_to_a_fingerprint(minutiae, core_points)

    # Generate fingerprint object using data of client from DB
    client_fingerprint = get_client_fingerprint(db, r_id_client)

    # Auth movement using fingerprints
    r_auth_fingerprint = await auth_fingerprint
    result = await validate_operation_by_fingerprints(
        auth_fingerprint=r_auth_fingerprint,
        client_fingerprint=await client_fingerprint,
        identifier=id_movement,
        type_s='MOV',
        r=r
    )
    if not result:
        try:
            add_attempt_cache(r, id_movement, 'MOV')
        except HTTPException as he:
            if he.status_code == status.HTTP_403_FORBIDDEN:
                finish_movement_unsuccessfully(db, id_movement=id_movement)
                await delete_performer_in_cache(r, 'MOV', id_movement)
                raise he
            else:
                show_error_message(he)
                raise compile_exception
        except Exception as e:
            show_error_message(e)
            raise compile_exception

        r_auth_fingerprint.show_message(r_auth_fingerprint.DONT_MATCH_FINGERPRINT, True)
    else:
        bt.add_task(
            erase_attempt_cache,
            r=r,
            identifier=id_movement,
            type_s='MOV'
        )
        await save_authentication_movement_result_in_cache(r, id_movement, TypeAuthFrom.fingerprint)

    response = BasicResponse(
        operation="Authorize movement",
        successful=result
    )

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/movement/user/{id_user}/payments',
    response_model=Union[SecureBase, PaymentComplexList],
    status_code=status.HTTP_200_OK
)
async def get_payments_of_user(
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if current_token.id_user != id_user:
        raise not_authorized_exception

    if current_token.type_user == TypeUser.client.value:
        response = get_payments_of_client(db, current_token.id_type)
    elif current_token.type_user == TypeUser.market.value or current_token.type_user == TypeUser.system.value:
        response = get_payments_of_market(db, current_token.id_type)
    else:
        raise type_of_value_not_compatible

    if secure:
        secure_response = cipher_response_message(db=db, id_user=id_user, response=response)
        return secure_response

    return response
