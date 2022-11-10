from typing import Union

from fastapi import APIRouter, Path, Depends, Query, Body
from pydantic import ValidationError
from redis.client import Redis
from sqlalchemy.orm import Session
from starlette import status

from controller.credit_controller import get_credits, check_owner_credit, get_credit_description, generate_pre_credit
from controller.login_controller import get_current_token
from controller.secure_controller import cipher_response_message, get_data_from_secure
from core.cache import get_cache_client
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, validation_request_exception, type_of_user_not_compatible
from schemas.credit_base import ListCreditsDisplay, CreditBasicRequest
from schemas.credit_complex import CreditComplexProfile, CreditComplexSummary
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
