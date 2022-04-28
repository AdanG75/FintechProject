from fastapi import APIRouter, Body, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud.storage import Client
from starlette import status

from db.models.admins_db import DbAdmin
from db.orm import admins_orm
from db.storage import storage
from db.storage.tests import test_storage
from schemas.fingerprint_model import FingerprintSimpleModel
from web_utils.image_on_web import open_fingerprint_data_from_json, save_fingerprint_in_memory

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/tests/functions',
    tags=["tests"]
)

@router.get(
    path="/fingerprint/image",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse
)
async def get_fingerprint_image(
        request: Request,
        fingerprint_model: FingerprintSimpleModel = Body(...)
):
    fingerprint = save_fingerprint_in_memory(data_fingerprint=fingerprint_model.fingerprint)

    fingerprint_string = fingerprint.decode()

    return templates.TemplateResponse("raw_fingerprint.html", {"request": request, "fingerprint_img": fingerprint_string})


@router.get(
    path="/fingerprint/show",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse
)
async def show_fingerprint(
        request: Request
):
    fingerprint_data = open_fingerprint_data_from_json()

    fingerprint = save_fingerprint_in_memory(fingerprint_data)

    fingerprint_string = fingerprint.decode()

    return templates.TemplateResponse(
        "raw_fingerprint.html",
        {"request": request, "fingerprint_img": fingerprint_string}
    )


@router.post(
    path="/create/bucket_test",
    status_code=status.HTTP_200_OK
)
async def create_bucket(
        gcs: Client = Depends(storage.get_storage_client),
        current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
):
    response = test_storage.create_a_bucket_test(gcs=gcs)

    return response


@router.post(
    path="/save/fingerprint_image",
    status_code=status.HTTP_200_OK
)
async def save_fingerprint_into_bucket(
        fingerprint_model: FingerprintSimpleModel = Body(...),
        gcs: Client = Depends(storage.get_storage_client),
        current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
):
    fingerprint = save_fingerprint_in_memory(fingerprint_model.fingerprint, return_format="bytes")
    response = test_storage.save_fingerprint_into_bucket_test(
        gcs=gcs,
        fingerprint_data=fingerprint,
        data_format="bytes"
    )

    return response


@router.get(
    path="/download/fingerprint_image",
    status_code=status.HTTP_200_OK
)
async def download_fingerprint_from_bucket(
        gcs: Client = Depends(storage.get_storage_client),
        current_admin: DbAdmin = Depends(admins_orm.get_current_admin)
):

    response = test_storage.download_from_bucket_test(gcs=gcs)

    return response


