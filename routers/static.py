from fastapi import APIRouter, Path, Depends
from google.cloud.storage import Client
from starlette import status
from starlette.responses import RedirectResponse

from core.config import settings
from db.storage import storage

router = APIRouter(
    prefix="/static",
    tags=["static"]
)


@router.get(
    path="/{file}",
    status_code=status.HTTP_200_OK,
    response_class=RedirectResponse
)
def get_file(
        file: str = Path(..., min_length=4, max_length=42),
        gcs: Client = Depends(storage.get_storage_client)
):
    path = storage.get_file_path(
        blob_name=file,
        bucket_name=settings.get_server_bucket(),
        storage_client=gcs
    )

    return RedirectResponse(
        url=path
    )
