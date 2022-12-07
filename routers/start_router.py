from typing import Union, Optional

from fastapi import APIRouter, Body, Query, Depends, Path
from fastapi.security import OAuth2PasswordRequestForm
from google.cloud.storage.client import Client
from pydantic.error_wrappers import ValidationError
from redis.client import Redis
from sqlalchemy.orm import Session
from starlette import status
from starlette.background import BackgroundTasks

from controller.fingerprint_controller import register_fingerprint, does_client_have_fingerprints_samples_registered, \
    preregister_fingerprint, check_fingerprint_request
from controller.password_recovery_controller import generate_new_code_to_recover_password, check_code, change_password
from controller.secure_controller import get_data_from_secure, get_data_from_rsa_message, cipher_response_message
from controller import login_controller as c_login
from controller.login_controller import get_current_token
from controller.sign_up_controller import get_user_type, route_user_to_sign_up, check_quality_of_fingerprints
from core.app_email import send_register_email, send_recovery_code
from db.cache.cache import get_cache_client, item_save, item_get
from core.config import settings
from db.database import get_db
from db.orm.exceptions_orm import bad_quality_fingerprint_exception, not_valid_operation_exception, \
    wrong_code_exception, validation_request_exception, not_authorized_exception
from db.storage.storage import get_storage_client
from schemas.admin_complex import AdminFullDisplay, AdminFullRequest
from schemas.basic_response import BasicResponse, BasicTicketResponse, CodeRequest, ChangePasswordRequest
from schemas.client_complex import ClientFullDisplay, ClientFullRequest
from schemas.fingerprint_base import FingerprintBasicDisplay
from schemas.fingerprint_complex import FingerprintFullRequest
from schemas.market_complex import MarketFullRequest, MarketFullDisplay
from schemas.password_recovery_base import PasswordRecoveryRequest
from schemas.secure_base import SecureBase, PublicKeyBase, SecureRequest
from schemas.system_complex import SystemFullRequest, SystemFullDisplay
from schemas.token_base import TokenBase, TokenSummary
from schemas.type_user import TypeUser

router = APIRouter(
    tags=['main']
)


@router.post(
    path='/sign-up',
    response_model=Union[SecureBase, AdminFullDisplay, ClientFullDisplay,
                         MarketFullDisplay, SystemFullDisplay, BasicResponse],
    status_code=status.HTTP_201_CREATED
)
async def sing_up(
        bt: BackgroundTasks,
        request: Union[
            SecureRequest, AdminFullRequest, ClientFullRequest, MarketFullRequest, SystemFullRequest
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
        bt.add_task(
            send_register_email,
            email_user=response.user.email,
            id_user=response.user.id_user,
            name_user=response.user.name
        )

    if secure:
        if request.public_pem is None:
            return BasicResponse(
                operation="Register user",
                successful=True
            )

        secure_response = cipher_response_message(response, without_auth=True, user_pem=request.public_pem)
        return secure_response
    else:
        return response


@router.post(
    path='/fingerprint/pre-register/client/{id_client}',
    response_model=Union[SecureBase, BasicTicketResponse],
    status_code=status.HTTP_202_ACCEPTED
)
async def preregister_fingerprint_of_client(
        id_client: str = Path(..., min_length=12, max_length=40),
        request: Union[SecureRequest, FingerprintFullRequest] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client)
):
    if does_client_have_fingerprints_samples_registered(db, id_client):
        raise not_valid_operation_exception

    data_request = get_data_from_secure(request) if secure else request
    try:
        fps_request = FingerprintFullRequest.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    if fps_request.metadata.id_client != id_client:
        raise not_authorized_exception

    is_good, data = await check_quality_of_fingerprints(fps_request.samples)
    if is_good:
        ticket = preregister_fingerprint(id_client, data, fps_request, r, 'CLI')
    else:
        raise bad_quality_fingerprint_exception

    plain_response = BasicTicketResponse(
        ticket=ticket
    )

    if secure:
        if request.public_pem is None:
            return plain_response

        item_save(r, f'PEM-CLI-{id_client}', request.public_pem)
        secure_response = cipher_response_message(plain_response, without_auth=True, user_pem=request.public_pem)
        return secure_response

    return plain_response


@router.post(
    path='/fingerprint/register/client/{id_client}',
    response_model=Union[SecureBase, FingerprintBasicDisplay, BasicResponse],
    status_code=status.HTTP_201_CREATED
)
async def register_fingerprint_of_client(
        id_client: str = Path(..., min_length=12, max_length=40),
        request: Union[SecureRequest, BasicTicketResponse] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        gcs: Client = Depends(get_storage_client),
        r: Redis = Depends(get_cache_client)
):
    if does_client_have_fingerprints_samples_registered(db, id_client):
        raise not_valid_operation_exception

    data_request = get_data_from_secure(request) if secure else request
    try:
        ticket_request = BasicTicketResponse.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    fingerprint_request = check_fingerprint_request(id_client, ticket_request.ticket, r, 'CLI')

    fingerprint_response = await register_fingerprint(
        db=db,
        gcs=gcs,
        fingerprint_request=fingerprint_request.fingerprint_full_request,
        id_client=id_client,
        data_summary=fingerprint_request.summary
    )

    if secure:
        public_pem = item_get(r, f'PEM-CLI-{id_client}')
        if public_pem is None:
            return BasicResponse(
                operation="Register fingerprint",
                successful=True
            )

        secure_response = cipher_response_message(fingerprint_response, without_auth=True, user_pem=public_pem)
        return secure_response

    return fingerprint_response


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
    email = get_data_from_rsa_message(request.username) if secure else request.username
    password = get_data_from_rsa_message(request.password) if secure else request.password

    # Call login in controller/login
    token = c_login.login(db, email, password)

    return token


@router.delete(
    path="/logout",
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def logout(
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    result = c_login.logout(db, current_token.id_session)

    return BasicResponse(
        operation='Logout',
        successful=result
    )


@router.post(
    path='/forgot-password',
    response_model=Union[SecureBase, BasicResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_password_code(
        bt: BackgroundTasks,
        request: Union[SecureRequest, PasswordRecoveryRequest] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client)
):
    data_request = get_data_from_secure(request) if secure else request
    try:
        pr_request = PasswordRecoveryRequest.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    code = generate_new_code_to_recover_password(db, pr_request.email, r)

    bt.add_task(
        send_recovery_code,
        email_user=pr_request.email,
        code=code
    )

    basic_response = BasicResponse(
        operation='Generate password recovery code',
        successful=True
    )

    if secure:
        if request.public_pem is None:
            return basic_response

        secure_response = cipher_response_message(basic_response, without_auth=True, user_pem=request.public_pem)
        return secure_response

    return basic_response


@router.post(
    path='/forgot-password/validate',
    response_model=Union[SecureBase, BasicTicketResponse],
    status_code=status.HTTP_202_ACCEPTED
)
async def validate_code(
        request: Union[SecureRequest, CodeRequest],
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client)
):
    data_request = get_data_from_secure(request) if secure else request
    try:
        code_request = CodeRequest.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    ticket = check_code(db, code_request, r)
    if ticket is None:
        raise wrong_code_exception

    ticket_response = BasicTicketResponse(
        ticket=ticket
    )
    if secure:
        if request.public_pem is None:
            return ticket_response

        secure_response = cipher_response_message(ticket_response, without_auth=True, user_pem=request.public_pem)
        return secure_response

    return ticket_response


@router.patch(
    path='/recover-password',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK
)
async def change_password_request(
        request: Union[SecureRequest, ChangePasswordRequest] = Body(...),
        secure: bool = Query(True),
        db: Session = Depends(get_db),
        r: Redis = Depends(get_cache_client)
):
    data_request = get_data_from_secure(request) if secure else request
    try:
        pw_request = ChangePasswordRequest.parse_obj(data_request) if isinstance(data_request, dict) else data_request
    except ValidationError:
        raise validation_request_exception

    change_password(db, r, pw_request)
    response = BasicResponse(
        operation='Recover password',
        successful=True
    )

    if secure:
        if request.public_pem is None:
            return response

        secure_response = cipher_response_message(response, without_auth=True, user_pem=request.public_pem)
        return secure_response

    return response


@router.get(
    path='/public-key',
    response_model=PublicKeyBase,
    status_code=status.HTTP_200_OK
)
async def get_system_public_key():
    return PublicKeyBase(
        pem=settings.get_server_public_key()
    )
