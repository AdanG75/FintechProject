import base64
from typing import Union

from fastapi import HTTPException
from google.cloud import storage
from google.cloud.storage import Bucket
from google.cloud.storage.client import Client
from starlette import status


def get_storage_client() -> Client:
    """
    Provide the Cloud Storage Client

    :return: The Cloud Storage Client
    """
    storage_client: Client = storage.Client()

    try:
        yield storage_client
    finally:
        storage_client.close()


def create_bucket(bucket_name: str, storage_client: Client) -> bool:
    """
    Create a bucket for personal use

    :param bucket_name: (str) - bucket's name
    :param storage_client: (google.cloud.storage.client.Client) a client to bundle Cloud Storage's API

    :return: True if all were OK
    """
    try:
        # create a new bucket
        bucket = storage_client.bucket(bucket_name.lower())
        bucket.storage_class = "STANDARD"  # Archive | Nearline | Standard
        bucket.location = 'US-CENTRAL1'

        storage_client.create_bucket(bucket)  # returns Bucket object

        return True
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't communicate with cloud storage"
        )


def get_bucket(bucket_name: str, storage_client: Client) -> Bucket:
    """
    Return the bucket which have the name passed as parameter

    :param bucket_name: (str) - bucket's name
    :param storage_client: (google.cloud.storage.client.Client) a client to bundle Cloud Storage's API

    :return: (google.cloud.storage.Bucket) - The Bucket object
    """
    try:
        my_bucket = storage_client.get_bucket(bucket_name.lower())
        return my_bucket
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't communicate with cloud storage"
        )


def get_bucket_details(bucket_name: str, storage_client: Client) -> dict:
    """
        Return the bucket's detail which have the name passed as parameter

        :param bucket_name: (str) - bucket's name
        :param storage_client: (google.cloud.storage.client.Client) a client to bundle Cloud Storage's API

        :return: (dict) - The Bucket's detail name, id, location, created_at, storage_class (keys' name)
        """
    bucket = get_bucket(bucket_name=bucket_name, storage_client=storage_client)

    response = {
        "name": bucket.name,
        "id": bucket.id,
        "location": bucket.location,
        "created_at": str(bucket.time_created),
        "storage_class": bucket.storage_class
    }

    return response



def upload_file_to_bucket(
        blob_name: str,
        file_path: str,
        bucket_name: str,
        storage_client: Client
) -> bool:
    """
    Upload file to a bucket

    :param blob_name:  (str) - object's name
    :param file_path: (str) - location of the file including filename e.g. /home/images/fig.png
    :param bucket_name: (str) - bucket's name
    :param storage_client: (google.cloud.storage.client.Client) a client to bundle Cloud Storage's API

    :return: True if all were OK
    """
    try:
        bucket = storage_client.get_bucket(bucket_name.lower())
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)

        return True
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't communicate with cloud storage"
        )


def upload_bytes_or_string_file_to_bucket(
        blob_name: str,
        bucket_name: str,
        data: Union[bytes, str],
        storage_client: Client
) -> bool:
    """
    Upload file encoded on base64 to a bucket

    :param blob_name:  (str) - object's name
    :param bucket_name: (str) - bucket's name
    :param data: (Union[bytes, str]) - bytes or string that represent the object's data
    :param storage_client: (google.cloud.storage.client.Client) a client to bundle Cloud Storage's API

    :return: True if all were OK
    """

    try:
        bucket = storage_client.get_bucket(bucket_name.lower())
        blob = bucket.blob(blob_name)

        blob.upload_from_string(
            data=data,
            content_type="image/bmp"
        )

        return True
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't communicate with cloud storage"
        )


def upload_base64_file_to_bucket(
        blob_name: str,
        bucket_name: str,
        data: bytes,
        storage_client: Client
) -> bool:
    """
    Upload file encoded on base64 to a bucket

    :param blob_name:  (str) - object's name
    :param bucket_name: (str) - bucket's name
    :param data: (bytes) - object's data in base64 format
    :param storage_client: (google.cloud.storage.client.Client) a client to bundle Cloud Storage's API

    :return: True if all were OK
    """
    file_str = data.decode()
    decode_data = base64.b64decode(file_str)

    result = upload_bytes_or_string_file_to_bucket(
        blob_name=blob_name,
        bucket_name=bucket_name,
        data=decode_data,
        storage_client=storage_client
    )

    return result



def download_file_from_bucket(
        blob_name: str,
        file_path: str,
        bucket_name: str,
        storage_client: Client
) -> bool:
    """
    Download a file (blob_name) from selected bucked (bucket_name) to the destination directory (file_path)

    :param blob_name: (str) - object's name
    :param file_path: (str) - location where the file will be saved e.g. /home/images/
    :param bucket_name: (str) - bucket's name
    :param storage_client: (google.cloud.storage.client.Client) a client to bundle Cloud Storage's API

    :return: True if all were OK
    """
    try:
        bucket = storage_client.get_bucket(bucket_name.lower())
        blob = bucket.blob(blob_name)

        with open(file_path, 'wb') as f:
            storage_client.download_blob_to_file(blob, f)

        print('Saved')
        return True
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't communicate with cloud storage"
        )
