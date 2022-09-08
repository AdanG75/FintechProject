import os.path

from fastapi import HTTPException
from google.cloud.storage.client import Client
from starlette import status

from db.storage import storage

user_bucket = "CLI-c75812d0b9d14ef3b37622f256c63aa9"


def create_a_bucket_test(gcs: Client):
    result = storage.create_bucket(bucket_name=user_bucket, storage_client=gcs)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System couldn't create bucket"
        )

    return {"bucket_name": user_bucket}


def save_fingerprint_into_bucket_test(gcs: Client, fingerprint_data: bytes, data_format='base64'):
    blob_name = "test_fingerprint3"

    if data_format == 'base64':
        result = storage.upload_base64_file_to_bucket(
            blob_name=blob_name,
            bucket_name=user_bucket,
            data=fingerprint_data,
            storage_client=gcs
        )
    elif data_format == 'bytes':
        result = storage.upload_bytes_or_string_file_to_bucket(
            blob_name=blob_name,
            bucket_name=user_bucket,
            data=fingerprint_data,
            storage_client=gcs
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="Format type not available"
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System couldn't save fingerprint image"
        )

    return {
        "bucket_name": user_bucket,
        "file_saved": blob_name
    }


def download_from_bucket_test(gcs: Client):
    name_fingerprint_file = "enhance-Main-fingerprint"
    name_fingerprint_file_with_extension = name_fingerprint_file + ".bmp"

    result = storage.download_file_from_bucket(
        blob_name=name_fingerprint_file,
        file_path=os.path.join(os.getcwd(), name_fingerprint_file_with_extension),
        bucket_name="CLI-f83ffeb361c940dd95a9ea9fc756888b",
        storage_client=gcs
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System couldn't get fingerprint image"
        )

    return {
        "file_name": name_fingerprint_file_with_extension,
        "directory": os.getcwd()
    }


def get_bucket_details_test(gcs: Client):
    details = storage.get_bucket_details(bucket_name=user_bucket, storage_client=gcs)

    return details
