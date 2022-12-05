from typing import Union

from fastapi import APIRouter, Path, Depends, Query, Body, HTTPException
from pydantic import ValidationError
from redis.client import Redis
from sqlalchemy.orm import Session
from starlette import status
from starlette.background import BackgroundTasks

from controller.credit_controller import get_credits, check_owner_credit, get_credit_description, generate_pre_credit, \
    save_precredit_fingerprint, get_pre_credit_request_from_cache, new_credit, \
    delete_pre_credit_requester_and_performer_in_cache, approve_credit_market
from controller.fingerprint_controller import set_minutiae_and_core_points_to_a_fingerprint, get_client_fingerprint, \
    validate_credit_by_fingerprints
from controller.general_controller import check_performer_in_cache, get_fingerprint_auth_data, \
    get_requester_from_cache, add_attempt_cache, erase_attempt_cache, save_auth_result, check_auth_result, \
    delete_auth_resul, delete_fingerprint_auth_data
from controller.login_controller import get_current_token
from controller.secure_controller import cipher_response_message, get_data_from_secure
from controller.user_controller import get_email_based_on_id_type, get_name_of_market
from core.app_email import send_new_credit_email
from core.cache import get_cache_client
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, validation_request_exception, type_of_user_not_compatible, \
    not_longer_available_exception, only_available_market_exception
from schemas.basic_response import BasicResponse
from schemas.credit_base import ListCreditsDisplay, CreditBasicRequest, CreditDisplay
from schemas.credit_complex import CreditComplexProfile, CreditComplexSummary
from schemas.fingerprint_model import FingerprintB64
from schemas.secure_base import SecureBase
from schemas.token_base import TokenSummary
from schemas.type_user import TypeUser

router = APIRouter(
    tags=['credit']
)


@router.get(
    path='/credit/{id_credit}',
    response_model=Union[SecureBase, CreditComplexProfile],
    status_code=status.HTTP_200_OK
)
async def get_description_of_credit(
        id_credit: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_owner_credit(db, id_credit, current_token.type_user, current_token.id_type):
        raise not_authorized_exception

    response = await get_credit_description(db, id_credit, current_token.type_user)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/credit/user/{id_user}',
    response_model=Union[SecureBase, ListCreditsDisplay],
    status_code=status.HTTP_200_OK
)
async def get_credits_of_user(
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if id_user != current_token.id_user:
        raise not_authorized_exception

    user_credits = get_credits(db, current_token.type_user, current_token.id_type)
    credits_response = ListCreditsDisplay(
        credits=user_credits
    )

    if secure:
        secure_response = cipher_response_message(db=db, id_user=id_user, response=credits_response)
        return secure_response

    return credits_response


@router.post(
    path='/credit/order',
    response_model=Union[SecureBase, CreditComplexSummary],
    status_code=status.HTTP_201_CREATED
)
async def create_credit_order(
        request: Union[SecureBase, CreditBasicRequest] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    data_request = get_data_from_secure(request) if secure else request
    try:
        credit_request = CreditBasicRequest.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    # If type of user is market or system, system will approve the credit unless the actual performer was
    # different to request's market
    if current_token.type_user == TypeUser.market.value or current_token.type_user == TypeUser.system.value:
        if current_token.id_type != credit_request.id_market:
            raise not_authorized_exception

        is_approved = True
    else:
        if current_token.id_type != credit_request.id_client:
            raise not_authorized_exception

        is_approved = False

    if current_token.type_user == TypeUser.admin.value:
        raise type_of_user_not_compatible

    response = await generate_pre_credit(db, r, credit_request, current_token.id_user, is_approved)

    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.post(
    path='/credit/order/{id_order}/fingerprint',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_202_ACCEPTED
)
async def save_fingerprint_to_authorize_pre_credit(
        id_order: str = Path(..., min_length=16, max_length=48),
        request: Union[SecureBase, FingerprintB64] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    is_performer = check_performer_in_cache(r, id_order, 'CRT', current_token.id_user)

    if is_performer is False:
        raise not_authorized_exception

    if is_performer is None:
        raise not_longer_available_exception

    data_request = get_data_from_secure(request) if secure else request
    try:
        fingerprint_request = FingerprintB64.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    result = await save_precredit_fingerprint(r, id_order, fingerprint_request)

    response = BasicResponse(
        operation="Save pre-credit fingerprint",
        successful=result
    )
    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/credit/order/{id_order}/match',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_200_OK
)
async def validate_by_fingerprint(
        id_order: str = Path(..., min_length=16, max_length=48),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    is_performer = check_performer_in_cache(r, id_order, 'CRT', current_token.id_user)

    if is_performer is False:
        raise not_authorized_exception

    if is_performer is None:
        raise not_longer_available_exception

    id_client = get_requester_from_cache(r, 'CRT', id_order)

    # Get minutiae and core points from cache
    minutiae, core_points = get_fingerprint_auth_data(r, 'CRT', id_order)

    # Generate fingerprint object using minutiae and core points
    auth_fingerprint = await set_minutiae_and_core_points_to_a_fingerprint(minutiae, core_points)

    # Generate fingerprint object using data of client from DB
    client_fingerprint = await get_client_fingerprint(db, id_client)

    # Auth credit using fingerprints
    result = await validate_credit_by_fingerprints(auth_fingerprint, client_fingerprint, id_order, r)
    if not result:
        try:
            add_attempt_cache(r, id_order, 'CRT')
        except HTTPException as e:
            await delete_pre_credit_requester_and_performer_in_cache(r, id_order)
            raise e

        auth_fingerprint.show_message(auth_fingerprint.DONT_MATCH_FINGERPRINT, True)
    else:
        save_auth_result(r, id_order, 'CRT', result)
        erase_attempt_cache(r, id_order, 'CRT')

    response = BasicResponse(
        operation="Authorize credit",
        successful=result
    )
    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.post(
    path='/credit/order/{id_order}/capture',
    response_model=Union[SecureBase, CreditDisplay],
    status_code=status.HTTP_201_CREATED
)
async def create_credit(
        bt: BackgroundTasks,
        id_order: str = Path(..., min_length=16, max_length=48),
        secure: bool = Query(True),
        notify: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    is_performer = check_performer_in_cache(r, id_order, 'CRT', current_token.id_user)

    if is_performer is False:
        raise not_authorized_exception

    if is_performer is None:
        raise not_longer_available_exception

    if not check_auth_result(r, id_order, 'CRT'):
        raise not_authorized_exception

    # Get credit request from cache
    credit_request = get_pre_credit_request_from_cache(r, id_order, 'CRT')

    # Create credit
    response = await new_credit(db, credit_request, current_token.type_user)

    # Notify user
    if current_token.type_user == TypeUser.market.value or current_token.type_user == TypeUser.system.value:
        notify = True

    if notify:
        client_email = await get_email_based_on_id_type(db, response.id_client, str(TypeUser.client.value))
        market_name = await get_name_of_market(db, response.id_market)
        bt.add_task(
            send_new_credit_email,
            email_user=client_email,
            approved=response.is_approved,
            market_name=market_name,
            amount=response.amount
        )

    # delete data in cache
    bt.add_task(
        delete_pre_credit_requester_and_performer_in_cache,
        r=r,
        identifier=id_order
    )
    bt.add_task(
        delete_auth_resul,
        r=r,
        identifier=id_order,
        type_s='CRT'
    )

    # send response
    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.delete(
    path='/credit/order/{id_order}',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_200_OK
)
async def delete_pre_credit(
        id_order: str = Path(..., min_length=16, max_length=48),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    is_performer = check_performer_in_cache(r, id_order, 'CRT', current_token.id_user)

    if is_performer is False:
        raise not_authorized_exception

    if is_performer is None:
        raise not_longer_available_exception

    result = await delete_pre_credit_requester_and_performer_in_cache(r, id_order, 'CRT')
    await delete_fingerprint_auth_data(r, 'CRT', id_order)
    await delete_auth_resul(r, id_order, 'CRT')
    response = BasicResponse(
        operation="Delete credit order",
        successful=result
    )
    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response


@router.patch(
    path='/credit/{id_credit}/approve',
    response_model=Union[SecureBase, CreditDisplay],
    status_code=status.HTTP_200_OK
)
async def approve_credit(
        id_credit: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not (current_token.type_user == TypeUser.market.value or current_token.type_user == TypeUser.system.value):
        raise only_available_market_exception

    if not check_owner_credit(db, id_credit, current_token.type_user, current_token.id_type):
        raise not_authorized_exception

    response = await approve_credit_market(db, id_credit)
    if secure:
        secure_response = cipher_response_message(db=db, id_user=current_token.id_user, response=response)
        return secure_response

    return response
