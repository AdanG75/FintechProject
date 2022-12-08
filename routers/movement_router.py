from typing import Union

from fastapi import APIRouter, Depends, Path, Query, Body
from pydantic import ValidationError
from redis.client import Redis
from sqlalchemy.orm import Session
from starlette import status

from controller.credit_controller import get_id_of_owners_of_credit
from controller.general_controller import save_value_in_cache_with_formatted_name
from controller.login_controller import get_current_token, get_logged_user_to_make_movement
from controller.movement_controller import get_payments_of_client, get_payments_of_market, create_summary_of_movement, \
    make_movement_based_on_type, finish_movement_unsuccessfully
from controller.secure_controller import cipher_response_message, get_data_from_secure
from core.logs import show_error_message
from db.cache.cache import get_cache_client
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, type_of_value_not_compatible, \
    validation_request_exception, cache_exception, compile_exception
from schemas.movement_base import MovementTypeRequest
from schemas.movement_complex import MovementExtraRequest, BasicExtraMovement
from schemas.payment_base import PaymentComplexList
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary
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

    # Save performer if a response is created
    try:
        cache_result = await save_value_in_cache_with_formatted_name(
            r, 'PFR', 'MOV', response.id_movement, current_token.id_user, 3600
        )
    except ValueError as e:
        show_error_message(e)
        finish_movement_unsuccessfully(db, id_movement=response.id_movement)
        raise compile_exception

    if not cache_result:
        finish_movement_unsuccessfully(db, id_movement=response.id_movement)
        raise cache_exception

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
