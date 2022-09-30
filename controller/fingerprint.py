from typing import List, Optional

from google.cloud.storage.client import Client
from redis.client import Redis
from sqlalchemy.orm import Session

from controller.bucket import create_bucket_and_save_samples_from_fingerprint
from controller.sign_up import select_the_best_sample
from core.cache import is_the_same, batch_save
from core.utils import generate_random_string
from db.models.fingerprints_db import DbFingerprint
from db.orm.clients_orm import get_client_by_id_client
from db.orm.cores_orm import insert_list_of_core_points
from db.orm.exceptions_orm import uncreated_bucked_exception, compile_exception, uncreated_fingerprint_exception, \
    NotFoundException, wrong_data_sent_exception, expired_cache_exception, expired_ticket_or_is_incorrect_exception
from db.orm.fingerprints_orm import create_fingerprint, get_fingerprints_by_id_client
from db.orm.functions_orm import full_database_exceptions, multiple_attempts
from db.orm.minutiae_orm import insert_list_of_minutiae
from fingerprint_process.description.fingerprint import Fingerprint
from fingerprint_process.utils.error_message import ErrorMessage
from fingerprint_process.utils.utils import get_description_fingerprint
from schemas.fingerprint_base import FingerprintBase, FingerprintBasicDisplay, FingerprintRequest, ClientInner
from schemas.fingerprint_complex import FingerprintFullRequest, FingerprintRegisterRequest
from schemas.fingerprint_model import FingerprintSamples
from secure.cipher_secure import cipher_data, decipher_data


async def register_fingerprint(
        db: Session,
        gcs: Client,
        fingerprint_request: FingerprintFullRequest,
        id_client: str,
        data_summary: List[dict]
) -> Optional[FingerprintBasicDisplay]:
    # Get fingerprint's samples
    fingerprints: FingerprintSamples = fingerprint_request.samples

    # Get best sample
    position_best_sample = select_the_best_sample(data_summary)
    best_sample = fingerprints.fingerprints[position_best_sample]

    # Describe sample of fingerprint
    result = get_description_fingerprint(
        name_fingerprint='example',
        source='api',
        data_fingerprint=best_sample,
        mode='register',
        show_result=False,
        save_result=False
    )

    # Check if there is an error
    if isinstance(result, int):
        console = ErrorMessage()
        console.show_message(result, web=True)

    # If result is a fingerprint object we save the images and the characteristic data into the DB
    if isinstance(result, Fingerprint):
        url_sample, was_successful = create_bucket_and_save_samples_from_fingerprint(
            gcs,
            fingerprint=result,
            id_client=id_client,
            alias_fingerprint=fingerprint_request.metadata.alias_fingerprint
        )

        if not was_successful:
            raise uncreated_bucked_exception

        # Here we save the characteristic data into DB
        fingerprint_request.metadata.id_client = id_client
        response = save_fingerprint_into_database(
            db,
            request=fingerprint_request.metadata,
            fingerprint=result,
            url_fingerprint=url_sample,
            quality='good'  # We can be sure that quality of the sample is good
        )

        return response
    else:
        raise uncreated_fingerprint_exception


@multiple_attempts
@full_database_exceptions
def save_fingerprint_into_database(
        db: Session,
        request: FingerprintBase,
        fingerprint: Fingerprint,
        url_fingerprint: str,
        quality: str = 'good'
) -> FingerprintBasicDisplay:

    fingerprint_request = FingerprintRequest(
        id_client=request.id_client,
        alias_fingerprint=request.alias_fingerprint,
        main_fingerprint=request.main_fingerprint,
        url_fingerprint=url_fingerprint,
        fingerprint_type='auth',
        quality=quality,
        spectral_index=fingerprint.get_spectral_index(),
        spatial_index=fingerprint.get_spatial_index()
    )

    try:
        # Save fingerprint
        new_fingerprint: DbFingerprint = create_fingerprint(db, fingerprint_request, 'wait')
        db.begin_nested()
        db.refresh(new_fingerprint)

        # Insert Minutiae
        was_successful = insert_list_of_minutiae(
            db,
            minutiae=fingerprint.get_minutiae_list(),
            id_fingerprint=new_fingerprint.id_fingerprint,
            execute='wait'
        )

        if not was_successful:
            raise compile_exception

        # Insert core points
        was_successful = insert_list_of_core_points(
            db,
            core_points=fingerprint.get_core_point_list(),
            id_fingerprint=new_fingerprint.id_fingerprint,
            execute='wait'
        )

        if not was_successful:
            raise compile_exception

        # Save all changes
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    client = get_client_by_id_client(db, new_fingerprint.id_client)

    return FingerprintBasicDisplay(
        id_fingerprint=new_fingerprint.id_fingerprint,
        id_client=new_fingerprint.id_client,
        alias_fingerprint=new_fingerprint.alias_fingerprint,
        main_fingerprint=new_fingerprint.main_fingerprint,
        created_time=new_fingerprint.created_time,
        client=ClientInner(
            id_client=client.id_client,
            id_user=client.id_user
        )
    )


def does_client_have_fingerprints_samples_registered(db: Session, id_client: str) -> bool:
    try:
        get_client_by_id_client(db, id_client)
    except NotFoundException:
        raise wrong_data_sent_exception

    # Check if client have a fingerprint sample registered
    try:
        get_fingerprints_by_id_client(db, id_client)
    except NotFoundException:
        return False
    else:
        return True


def preregister_fingerprint(
        id_client: str,
        summary: list[dict],
        request: FingerprintFullRequest,
        r: Redis
) -> str:
    register_model = FingerprintRegisterRequest(
        fingerprint_full_request=request,
        summary=summary
    )

    # Cipher fingerprint's data to secure it
    secure_data = cipher_data(register_model.json())
    # Generate a ticket to ensure client authentication
    ticket: str = generate_random_string(8)

    # Save both fingerprint's data and client's ticket into cache
    values_to_catching = {
        f'PRE-{id_client}': secure_data,
        f'TKT-{id_client}': ticket
    }
    batch_save(r, values_to_catching)

    return ticket


def check_fingerprint_request(
        id_client: str,
        ticket: str,
        r: Redis
) -> FingerprintRegisterRequest:
    cache_ticket = r.get(f'TKT-{id_client}')
    if cache_ticket is not None:
        if is_the_same(cache_ticket, ticket):
            secure_data = r.get(f'PRE-{id_client}')
            if secure_data is None:
                raise expired_cache_exception

            secure_data_str = secure_data.decode('utf-8')
            json_data = decipher_data(secure_data_str)

            return FingerprintRegisterRequest.parse_raw(json_data)
        else:
            raise expired_ticket_or_is_incorrect_exception
    else:
        raise expired_cache_exception
