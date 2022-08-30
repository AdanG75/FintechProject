from typing import Union, Optional

from fastapi import APIRouter, Body, Query, Depends
from sqlalchemy.orm import Session
from starlette import status

from controller.sign_up import sign_up_admin
from core.config import settings
from db.database import get_db
from db.orm.exceptions_orm import type_of_value_not_compatible, wrong_data_sent_exception
from schemas.admin_complex import AdminFullDisplay, AdminFullRequest
from schemas.secure_base import SecureBase, PublicKeyBase
from schemas.type_user import TypeUser
from secure.cipher_secure import unpack_and_decrypt_data

router = APIRouter(
    tags=['main']
)


@router.post(
    path='/sign-up/',
    response_model=Union[SecureBase, AdminFullDisplay],
    status_code=status.HTTP_201_CREATED
)
async def sing_up(
        request: Union[SecureBase, AdminFullRequest] = Body(...),
        secure: Optional[bool] = Query(False),
        type_user: Optional[TypeUser] = Query(None),
        notify: Optional[bool] = Query(True),
        db: Session = Depends(get_db)
):
    if secure:
        if isinstance(request, SecureBase):
            receive_data = unpack_and_decrypt_data(request.dict())
        else:
            raise type_of_value_not_compatible

        if type_user is None:
            type_user = receive_data['user']['type_user']
            try:
                TypeUser(type_user)
            except ValueError:
                raise wrong_data_sent_exception

    else:
        if type_user is None:
            if not isinstance(request, SecureBase):
                type_user = request.user.type_user
            else:
                raise type_of_value_not_compatible

    if type_user.value == 'admin':
        response = await sign_up_admin(db, request)

    return response


@router.get(
    path='/public-key/',
    response_model=PublicKeyBase,
    status_code=status.HTTP_200_OK
)
async def get_system_public_key():
    return PublicKeyBase(
        pem=settings.get_server_public_key()
    )
