from typing import Optional

from fastapi import APIRouter, Body, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud.storage import Client
from sqlalchemy.orm import Session
from starlette import status

from core.utils import get_current_utc_timestamp
from db.database import get_db
from db.models.admins_db import DbAdmin
from db.orm import admins_orm
from db.storage import storage
from db.storage.tests import test_storage
from schemas.fingerprint_model import FingerprintSimpleModel
from schemas.message_model import MessageDisplay
from schemas.secure_base import SecureBase
from schemas.storage_base import StorageBase
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
        gcs: Client = Depends(storage.get_storage_client)
):
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
        gcs: Client = Depends(storage.get_storage_client)
):
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
        gcs: Client = Depends(storage.get_storage_client)
):
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
        gcs: Client = Depends(storage.get_storage_client)
):

    response = test_storage.download_from_bucket_test(gcs=gcs)

    return response


# Secure endpoint
# @router.post(
#     path="/secure",
#     status_code=status.HTTP_200_OK,
#     response_model=SecureBase,
#     tags=["secure"]
# )
# async def secure_message(
#         message: SecureBase = Body(...),
#         db: Session = Depends(get_db),
#         current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
# ):
#     public_key_pem: Optional[str] = current_admin.public_key
#
#     if public_key_pem is None or public_key_pem.isspace() or public_key_pem == '':
#         raise HTTPException(
#             status_code=status.HTTP_418_IM_A_TEAPOT,
#             detail="The operation need a saved public key into admin's data."
#         )
#
#     receive_data: dict = unpack_and_decrypt_data(message.dict())
#
#     send_data = MessageDisplay(
#         message="Receive message.\nWe will take the world.",
#         datetime=get_current_utc_timestamp(),
#         user="Server"
#     )
#
#     response: dict = pack_and_encrypt_data(send_data.dict(), public_key_pem)
#
#     return response

