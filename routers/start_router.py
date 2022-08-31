from typing import Union, Optional

from fastapi import APIRouter, Body, Query, Depends
from sqlalchemy.orm import Session
from starlette import status

from controller.general import get_data_from_secure
from controller.sign_up import get_user_type, route_user_to_sign_up
from core.config import settings
from db.database import get_db
from schemas.admin_complex import AdminFullDisplay, AdminFullRequest
from schemas.secure_base import SecureBase, PublicKeyBase
from schemas.type_user import TypeUser

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
    data = get_data_from_secure(request) if secure else request
    type_user = get_user_type(data) if type_user is None else type_user
    response = await route_user_to_sign_up(db, data, type_user)

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
