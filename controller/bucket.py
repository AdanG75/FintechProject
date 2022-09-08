from typing import Tuple

from google.cloud.storage.client import Client

from core.logs import write_data_log
from core.utils import replace_spaces_with_hyphens, generate_random_string
from db.orm.exceptions_orm import uncreated_bucked_exception, option_not_found_exception
from db.storage import storage
from fingerprint_process.description.fingerprint import Fingerprint
from schemas.storage_base import StorageSimple, StorageSimpleFile, StorageBase
from web_utils.image_on_web import save_fingerprint_in_memory


def create_bucket(gcs: Client, name_bucket: str) -> StorageSimple:
    result = storage.create_bucket(bucket_name=name_bucket, storage_client=gcs)

    if not result:
        raise uncreated_bucked_exception

    return StorageSimple(
        bucket_name=name_bucket
    )


def save_fingerprint_into_bucket(
        gcs: Client,
        fingerprint_data: bytes,
        bucket_name: str,
        blob_name: str,
        data_format: str = 'bytes'
) -> StorageSimpleFile:
    if data_format == 'base64':
        result = storage.upload_base64_file_to_bucket(
            blob_name=blob_name,
            bucket_name=bucket_name,
            data=fingerprint_data,
            storage_client=gcs
        )
    elif data_format == 'bytes':
        result = storage.upload_bytes_or_string_file_to_bucket(
            blob_name=blob_name,
            bucket_name=bucket_name,
            data=fingerprint_data,
            storage_client=gcs
        )
    else:
        raise option_not_found_exception

    if not result:
        raise uncreated_bucked_exception

    return StorageSimpleFile(
        bucket_name=bucket_name,
        file_saved=blob_name
    )


def get_bucket_details(gcs: Client, bucket_name: str) -> StorageBase:
    details = storage.get_bucket_details(bucket_name=bucket_name, storage_client=gcs)

    return StorageBase(
        name=details["name"],
        id=details["id"],
        location=details["location"],
        created_at=details["created_at"],
        storage_class=details["storage_class"]
    )


def create_bucket_and_save_samples_from_fingerprint(
        gcs: Client,
        fingerprint: Fingerprint,
        id_client: str,
        alias_fingerprint: str
) -> Tuple[str, bool]:
    try:
        create_bucket(gcs, name_bucket=id_client)

        image_base_name = replace_spaces_with_hyphens(alias_fingerprint)
        end_str = generate_random_string(5)
        raw_name = f'raw-{image_base_name}-{end_str}'
        enhance_name = f'enhance-{image_base_name}-{end_str}'

        raw_fingerprint: bytes = save_fingerprint_in_memory(
            image_fingerprint=fingerprint.get_raw_fingerprint_image(),
            return_format="bytes"
        )
        save_fingerprint_into_bucket(
            gcs=gcs,
            fingerprint_data=raw_fingerprint,
            bucket_name=id_client,
            blob_name=raw_name,
            data_format='bytes'
        )
        enhance_fingerprint: bytes = save_fingerprint_in_memory(
            image_fingerprint=fingerprint.get_fingerprint_image(),
            return_format="bytes"
        )
        save_fingerprint_into_bucket(
            gcs=gcs,
            fingerprint_data=enhance_fingerprint,
            bucket_name=id_client,
            blob_name=enhance_name,
            data_format='bytes'
        )
    except Exception as e:
        write_data_log(e.__str__(), severity="ERROR")
        print(e)
        return '', False

    url_fingerprint = f'{id_client.lower()}/{raw_name}'
    return url_fingerprint, True

