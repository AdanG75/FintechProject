from typing import List, Optional, Union

from google.cloud.storage.client import Client
from redis.client import Redis
from sqlalchemy.orm import Session

from controller.bucket_controller import create_bucket_and_save_samples_from_fingerprint
from controller.characteristic_point_controller import parse_db_list_to_cp_list
from controller.general_controller import delete_fingerprint_auth_data
from controller.sign_up_controller import select_the_best_sample
from core.cache import is_the_same, batch_save
from core.utils import generate_random_string
from db.models.fingerprints_db import DbFingerprint
from db.orm.clients_orm import get_client_by_id_client
from db.orm.cores_orm import insert_list_of_core_points, get_core_points_by_id_fingerprint
from db.orm.exceptions_orm import uncreated_bucked_exception, compile_exception, uncreated_fingerprint_exception, \
    NotFoundException, wrong_data_sent_exception, expired_cache_exception, expired_ticket_or_is_incorrect_exception, \
    cache_exception
from db.orm.fingerprints_orm import create_fingerprint, get_fingerprints_by_id_client, get_main_fingerprint_of_client
from db.orm.functions_orm import full_database_exceptions, multiple_attempts
from db.orm.minutiae_orm import insert_list_of_minutiae, get_minutiae_by_id_fingerprint
from fingerprint_process.description.fingerprint import Fingerprint
from fingerprint_process.models.core_point import CorePoint
from fingerprint_process.models.minutia import Minutiae
from fingerprint_process.utils.error_message import ErrorMessage
from fingerprint_process.utils.utils import get_description_fingerprint, match_index_and_base_fingerprints
from schemas.fingerprint_base import FingerprintBase, FingerprintBasicDisplay, FingerprintRequest, ClientInner
from schemas.fingerprint_complex import FingerprintFullRequest, FingerprintRegisterRequest
from schemas.fingerprint_model import FingerprintSamples
from schemas.type_user import TypeUser
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

    # If result is a fingerprint object, we save the images and the characteristic data into the DB
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


async def describe_fingerprint_from_sample(sample: Union[str, List[int]]) -> Fingerprint:
    # Describe sample of fingerprint
    result = get_description_fingerprint(
        name_fingerprint='auth-fingerprint',
        source='api',
        data_fingerprint=sample,
        mode='auth',
        show_result=False,
        save_result=False
    )

    # Check if there is an error
    if isinstance(result, int):
        console = ErrorMessage()
        console.show_message(result, web=True)

    if isinstance(result, Fingerprint):
        return result
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
    result = batch_save(r, values_to_catching, seconds=1800)

    if result.count(False) > 0:
        raise cache_exception

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


def check_if_user_have_fingerprint_registered(db: Session, type_user: str, id_type: str) -> bool:
    if type_user == TypeUser.client.value:
        try:
            get_main_fingerprint_of_client(db, id_type)
        except NotFoundException:
            return False

    else:
        return False

    return True


async def validate_credit_by_fingerprints(
        auth_fingerprint: Fingerprint,
        client_fingerprint: Fingerprint,
        identifier: Union[str, int],
        r: Redis
) -> bool:
    result = match_index_and_base_fingerprints(
        base_name=client_fingerprint.get_name_of_fingerprint(),
        input_name=auth_fingerprint.get_name_of_fingerprint(),
        mode='core',
        source='api',
        base_fingerprint=client_fingerprint,
        input_fingerprint=auth_fingerprint
    )

    if result is True:
        return False

    if result != auth_fingerprint.MATCH_FINGERPRINT:
        return False

    # In this point the fingerprint was validated
    await delete_fingerprint_auth_data(r, identifier)

    return True


async def set_minutiae_and_core_points_to_a_fingerprint(
        minutiae: List[Minutiae],
        core_points: List[CorePoint],
        name_fingerprint: str = 'auth_fingerprint'
) -> Fingerprint:

    fingerprint = Fingerprint(
        characteritic_point_thresh=0.8,
        name_fingerprint=name_fingerprint,
        show_result=False,
        save_result=False
    )

    fingerprint.set_minutiae_list(minutiae),
    fingerprint.set_core_points_list(core_points)

    return fingerprint


async def get_client_fingerprint(db: Session, id_client: str) -> Fingerprint:
    main_fingerprint = get_main_fingerprint_of_client(db, id_client)

    try:
        minutiae_db = get_minutiae_by_id_fingerprint(db, main_fingerprint.id_fingerprint)
        minutiae_obj = parse_db_list_to_cp_list(minutiae_db, 'minutia')
    except NotFoundException:
        minutiae_obj = []

    try:
        core_points_db = get_core_points_by_id_fingerprint(db, main_fingerprint.id_fingerprint)
        core_points_obj = parse_db_list_to_cp_list(core_points_db, 'core')
    except NotFoundException:
        core_points_obj = []

    return await set_minutiae_and_core_points_to_a_fingerprint(
        minutiae=minutiae_obj,
        core_points=core_points_obj,
        name_fingerprint=main_fingerprint.alias_fingerprint
    )
