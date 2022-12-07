from typing import Optional, Union

from fastapi import APIRouter, Body, Request, Depends, Path, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud.storage import Client
from redis.client import Redis
from sqlalchemy.orm import Session
from starlette import status

from controller.login_controller import get_current_token, check_type_user
from core.app_email import send_email_from_system, send_register_email
from db.cache.cache import get_cache_client
from core.utils import get_current_utc_timestamp
from db.database import get_db
from db.orm.exceptions_orm import credentials_exception
from db.orm.users_orm import get_public_key_pem
from db.storage import storage
from db.storage.tests import test_storage
from schemas.basic_response import BasicResponse
from schemas.fingerprint_model import FingerprintSimpleModel
from schemas.message_model import MessageDisplay
from schemas.secure_base import SecureBase
from schemas.storage_base import StorageBase
from schemas.token_base import TokenSummary
from secure.cipher_secure import unpack_and_decrypt_data, pack_and_encrypt_data
from web_utils.image_on_web import open_fingerprint_data_from_json, save_fingerprint_in_memory

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/tests/functions',
    tags=["tests"]
)


@router.get(
    path="/fingerprint/image",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse,
    tags=["fingerprint"]
)
async def get_fingerprint_image(
        request: Request,
        fingerprint_model: FingerprintSimpleModel = Body(...)
):
    fingerprint = save_fingerprint_in_memory(data_fingerprint=fingerprint_model.fingerprint)

    fingerprint_string = fingerprint.decode()

    return templates.TemplateResponse(
        "raw_fingerprint.html",
        {"request": request, "fingerprint_img": fingerprint_string}
    )


@router.get(
    path="/fingerprint/show",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse,
    tags=["fingerprint"]
)
async def show_fingerprint(
        request: Request
):
    fingerprint_data = open_fingerprint_data_from_json()

    fingerprint = save_fingerprint_in_memory(data_fingerprint=fingerprint_data)

    fingerprint_string = fingerprint.decode()

    return templates.TemplateResponse(
        "raw_fingerprint.html",
        {"request": request, "fingerprint_img": fingerprint_string}
    )


# Secure endpoint
@router.post(
    path="/create/bucket-test",
    status_code=status.HTTP_200_OK,
    tags=["bucket"]
)
async def create_bucket(
        gcs: Client = Depends(storage.get_storage_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = test_storage.create_a_bucket_test(gcs=gcs)

    return response


# Secure endpoint
@router.get(
    path='/detail/bucket-test',
    status_code=status.HTTP_200_OK,
    response_model=StorageBase,
    tags=["bucket"]
)
async def get_bucket_details(
        gcs: Client = Depends(storage.get_storage_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = test_storage.get_bucket_details_test(gcs=gcs)

    return response


# Secure endpoint
@router.post(
    path="/save/fingerprint-image",
    status_code=status.HTTP_200_OK,
    tags=["fingerprint", "bucket"]
)
async def save_fingerprint_into_bucket(
        fingerprint_model: FingerprintSimpleModel = Body(...),
        gcs: Client = Depends(storage.get_storage_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    fingerprint = save_fingerprint_in_memory(data_fingerprint=fingerprint_model.fingerprint, return_format="bytes")
    response = test_storage.save_fingerprint_into_bucket_test(
        gcs=gcs,
        fingerprint_data=fingerprint,
        data_format="bytes"
    )

    return response


# Secure endpoint
@router.get(
    path="/download/fingerprint-image",
    status_code=status.HTTP_200_OK,
    tags=["fingerprint", "bucket"]
)
async def download_fingerprint_from_bucket(
        gcs: Client = Depends(storage.get_storage_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    response = test_storage.download_from_bucket_test(gcs=gcs)

    return response


# Secure endpoint
@router.post(
    path="/secure",
    status_code=status.HTTP_200_OK,
    response_model=SecureBase,
    tags=["secure"]
)
async def secure_message(
        message: SecureBase = Body(...),
        db: Session = Depends(get_db),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    receive_data: dict = unpack_and_decrypt_data(message.dict())
    print(receive_data)

    send_data = MessageDisplay(
        message="Receive message.\nWe will take the world.",
        datetime=get_current_utc_timestamp(),
        user="Server"
    )

    public_key_pem = get_public_key_pem(db, current_token.id_user)
    response: dict = pack_and_encrypt_data(send_data.dict(), public_key_pem)

    return response


@router.post(
    path='/email',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK,
    tags=['email']
)
async def send_email(
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    send_email_from_system('fintech75.official@gmail.com', 'Simple test', 'This is a simple test.\nPlease, not reply.')

    return BasicResponse(
        operation='Send Email',
        successful=True
    )


@router.post(
    path='/email-registered-example',
    response_model=BasicResponse,
    status_code=status.HTTP_200_OK,
    tags=['email']
)
async def register_email_example(
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    email_sent = await send_register_email('fintech75.official@gmail.com', 9, 'Juan')

    return BasicResponse(
        operation=f'Send Email: {email_sent["id"]}',
        successful=True
    )


@router.put(
    path='/cache/{key}',
    status_code=status.HTTP_200_OK,
    tags=['cache']
)
async def get_value_from_cache(
        key: str = Path(..., min_length=1, max_length=31),
        value: Optional[Union[str, int, float]] = Query(None, min_length=1, max_length=31),
        seconds: Optional[int] = Query(1, ge=1, le=600),
        r: Redis = Depends(get_cache_client),
        current_token: TokenSummary = Depends(get_current_token)
):
    if not check_type_user(current_token, is_a='admin'):
        raise credentials_exception

    current_value = r.get(key)
    created = False
    updated = False

    if current_value is None:
        value = 'Hello' if value is None else value
        r.setex(key, seconds, value)
        current_value = r.get(key)
        created = True
    else:
        if current_value.decode('utf-8') != value and value is not None:
            r.setex(key, seconds, value)
            current_value = r.get(key)
            updated = True

    return {
        'value': current_value.decode('utf-8'),
        'created': created,
        'updated': updated
    }
