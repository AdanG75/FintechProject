from typing import Union, Optional

from fastapi import APIRouter, Body, Query, Depends, Path
from fastapi.security import OAuth2PasswordRequestForm
from google.cloud.storage.client import Client
from sqlalchemy.orm import Session
from starlette import status
from starlette.background import BackgroundTasks

from controller.fingerprint import register_fingerprint
from controller.general import get_data_from_secure
from controller import login as c_login
from controller.sign_up import get_user_type, route_user_to_sign_up, check_quality_of_fingerprints
from core.config import settings
from db.database import get_db
from db.orm.exceptions_orm import bad_quality_fingerprint_exception
from db.storage.storage import get_storage_client
from schemas.admin_complex import AdminFullDisplay, AdminFullRequest
from schemas.basic_response import BasicResponse
from schemas.client_complex import ClientFullDisplay, ClientFullRequest
from schemas.fingerprint_complex import FingerprintFullRequest
from schemas.market_complex import MarketFullRequest, MarketFullDisplay
from schemas.secure_base import SecureBase, PublicKeyBase
from schemas.system_complex import SystemFullRequest, SystemFullDisplay
from schemas.token_base import TokenBase
from schemas.type_user import TypeUser
from secure.cipher_secure import decrypt_data

router = APIRouter(
    tags=['main']
)


@router.post(
    path='/sign-up/',
    response_model=Union[SecureBase, AdminFullDisplay, ClientFullDisplay, MarketFullDisplay, SystemFullDisplay],
    status_code=status.HTTP_201_CREATED
)
async def sing_up(
        request: Union[
            SecureBase, AdminFullRequest, ClientFullRequest, MarketFullRequest, SystemFullRequest
        ] = Body(...),
        secure: Optional[bool] = Query(True),
        type_user: Optional[TypeUser] = Query(None),
        notify: Optional[bool] = Query(True),
        test_mode: Optional[bool] = Query(True),
        db: Session = Depends(get_db)
):
    data = get_data_from_secure(request) if secure else request
    type_user = get_user_type(data) if type_user is None else type_user
    response = await route_user_to_sign_up(db, data, type_user, test_mode)

    if notify:
        # Send an email using a background task
        pass

    return response


@router.post(
    path='/fingerprint/client/{id_client}',
    response_model=BasicResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def register_fingerprint_of_client(
        bt: BackgroundTasks,
        id_client: str = Path(..., min_length=12, max_length=40),
        request: Union[SecureBase, FingerprintFullRequest] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        gcs: Client = Depends(get_storage_client)
):
    data_request = get_data_from_secure(request) if secure else request
    fps_request = FingerprintFullRequest.parse_obj(data_request) if isinstance(data_request, dict) else data_request

    is_good, data = await check_quality_of_fingerprints(fps_request.samples)
    if is_good:
        bt.add_task(
            register_fingerprint,
            db=db,
            gcs=gcs,
            fingerprint_request=fps_request,
            id_client=id_client,
            data_summary=data
        )

        return BasicResponse(
          operation='Check fingerprints',
          successful=True
        )
    else:
        raise bad_quality_fingerprint_exception


@router.post(
    path="/login",
    response_model=TokenBase,
    status_code=status.HTTP_200_OK
)
async def login(
        request: OAuth2PasswordRequestForm = Depends(),
        secure: bool = Query(True),
        db: Session = Depends(get_db)
):
    email = decrypt_data(request.username) if secure else request.username
    password = decrypt_data(request.password) if secure else request.password

    # Call login in controller/login
    token = c_login.login(db, email, password)

    return token


@router.get(
    path='/public-key/',
    response_model=PublicKeyBase,
    status_code=status.HTTP_200_OK
)
async def get_system_public_key():
    return PublicKeyBase(
        pem=settings.get_server_public_key()
    )
