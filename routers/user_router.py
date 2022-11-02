from typing import Union

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token
from controller.secure_controller import get_data_from_secure, cipher_response_message
from controller.user_controller import check_public_key_of_user, get_profile_of_user
from db.database import get_db
from db.orm.exceptions_orm import not_authorized_exception, validation_request_exception
from schemas.admin_complex import AdminFullDisplay
from schemas.basic_response import BasicResponse
from schemas.client_complex import ClientProfileDisplay
from schemas.market_complex import MarketProfileDisplay
from schemas.secure_base import SecureBase, PublicKeyBase
from schemas.token_base import TokenSummary
from schemas.user_base import UserBasicDisplay

router = APIRouter(
    tags=['user']
)


@router.put(
    path='/public-key/{id_user}',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_200_OK
)
async def check_user_public_key(
        request: Union[SecureBase, PublicKeyBase] = Body(...),
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if current_token.id_user != id_user:
        raise not_authorized_exception

    data_request = get_data_from_secure(request) if secure else request
    try:
        pem_request = PublicKeyBase.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    check_public_key_of_user(db, id_user, pem_request.pem)

    response = BasicResponse(
        operation='Check user\'s public key',
        successful=True
    )

    if secure:
        secure_response = cipher_response_message(db=db, id_user=id_user, response=response)
        return secure_response

    return response


@router.get(
    path='/user/{id_user}',
    response_model=Union[SecureBase, UserBasicDisplay, AdminFullDisplay, MarketProfileDisplay, ClientProfileDisplay],
    status_code=status.HTTP_200_OK
)
async def get_user_profile(
        id_user: int = Path(..., gt=0),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if id_user != current_token.id_user:
        raise not_authorized_exception

    response = get_profile_of_user(db, id_user, current_token.type_user)
    if secure:
        secure_response = cipher_response_message(db=db, id_user=id_user, response=response)
        return secure_response

    return response
