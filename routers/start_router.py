from typing import Union, Optional

from fastapi import APIRouter, Body, Query, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from controller.general import get_data_from_secure
from controller.sign_up import get_user_type, route_user_to_sign_up, check_quality_of_fingerprints
from core.config import settings
from db.database import get_db
from db.orm.exceptions_orm import bad_quality_fingerprint_exception
from schemas.admin_complex import AdminFullDisplay, AdminFullRequest
from schemas.basic_response import BasicResponse
from schemas.client_complex import ClientFullDisplay, ClientFullRequest
from schemas.fingerprint_model import FingerprintSamples
from schemas.market_complex import MarketFullRequest, MarketFullDisplay
from schemas.secure_base import SecureBase, PublicKeyBase
from schemas.system_complex import SystemFullRequest, SystemFullDisplay
from schemas.type_user import TypeUser

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

    return response


@router.post(
    path='/fingerprint/client/{id_client}',
    response_model=BasicResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def register_fingerprint_of_client(
        id_client: str = Path(..., min_length=12, max_length=40),
        request: Union[SecureBase, FingerprintSamples] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db)
):
    data_request = get_data_from_secure(request) if secure else request
    fps_request = FingerprintSamples.parse_obj(data_request) if isinstance(data_request, dict) else data_request

    is_good, data = await check_quality_of_fingerprints(fps_request)
    if is_good:
        print(data)
        return BasicResponse(
          operation='Check fingerprints',
          successful=True
        )
    else:
        raise bad_quality_fingerprint_exception


@router.get(
    path='/public-key/',
    response_model=PublicKeyBase,
    status_code=status.HTTP_200_OK
)
async def get_system_public_key():
    return PublicKeyBase(
        pem=settings.get_server_public_key()
    )