from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from db.models.addresses_db import DbAddress  # Don't erase because it is used by relationship
from db.models.branches_db import DbBranch  # Don't erase because it is used by relationship
from db.models.clients_db import DbClient  # Don't erase because it is used by relationship
from db.models.fingerprints_db import DbFingerprint
from db.models.markets_db import DbMarket  # Don't erase because it is used by relationship
from db.orm.clients_orm import get_client_by_id_client
from db.orm.exceptions_orm import element_not_found_exception, \
    not_unique_alias_exception, not_main_element_exception, option_not_found_exception, NotFoundException, \
    operation_need_a_precondition_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from schemas.basic_response import BasicResponse
from schemas.fingerprint_base import FingerprintRequest, FingerprintUpdateRequest


@multiple_attempts
@full_database_exceptions
def create_fingerprint(db: Session, request: FingerprintRequest, execute: str = 'now') -> DbFingerprint:
    try:
        get_client_fingerprint_by_alias(db, request.id_client, request.alias_fingerprint)
    except NotFoundException:
        try:
            actual_main_fingerprint = get_main_fingerprint_of_client(db, request.id_client)
            if request.main_fingerprint:
                actual_main_fingerprint.main_fingerprint = False
        except NotFoundException:
            # Ensure that at least one fingerprint is the main fingerprint
            request.main_fingerprint = True

        fingerprint_uuid = uuid.uuid4().hex
        id_fingerprint = f"FNP-{fingerprint_uuid}"

        new_fingerprint = DbFingerprint(
            id_fingerprint=id_fingerprint,
            id_client=request.id_client,
            alias_fingerprint=request.alias_fingerprint,
            url_fingerprint=request.url_fingerprint,
            fingerprint_type=request.fingerprint_type.value,
            quality=request.quality.value,
            spectral_index=request.spectral_index,
            spatial_index=request.spatial_index,
            main_fingerprint=request.main_fingerprint,
            created_time=datetime.utcnow(),
            dropped=False
        )

        try:
            db.add(new_fingerprint)
            if execute == 'now':
                db.commit()
                db.refresh(new_fingerprint)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_fingerprint

    raise not_unique_alias_exception


@full_database_exceptions
def get_fingerprint_by_id(db: Session, id_fingerprint: str, mode: str = 'active') -> DbFingerprint:
    try:
        if mode == 'active':
            fingerprint = db.query(DbFingerprint).where(
                DbFingerprint.id_fingerprint == id_fingerprint,
                DbFingerprint.dropped == False
            ).one_or_none()
        elif mode == 'all':
            fingerprint = db.query(DbFingerprint).where(
                DbFingerprint.id_fingerprint == id_fingerprint
            ).one_or_none()
        else:
            raise option_not_found_exception

    except Exception as e:
        print(e)
        raise e

    if fingerprint is None:
        raise element_not_found_exception

    return fingerprint


@full_database_exceptions
def get_fingerprints_by_id_client(db: Session, id_client: str, mode: str = 'active') -> List[DbFingerprint]:
    try:
        if mode == 'active':
            fingerprints = db.query(DbFingerprint).where(
                DbFingerprint.id_client == id_client,
                DbFingerprint.dropped == False
            ).all()
        elif mode == 'all':
            fingerprints = db.query(DbFingerprint).where(
                DbFingerprint.id_client == id_client
            ).all()
        else:
            raise option_not_found_exception

    except Exception as e:
        print(e)
        raise e

    if fingerprints is None or len(fingerprints) < 1:
        raise element_not_found_exception

    return fingerprints


@full_database_exceptions
def get_main_fingerprint_of_client(db: Session, id_client: str) -> DbFingerprint:
    try:
        fingerprint = db.query(DbFingerprint).where(
            DbFingerprint.id_client == id_client,
            DbFingerprint.main_fingerprint == True,
            DbFingerprint.dropped == False
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if fingerprint is None:
        raise element_not_found_exception

    return fingerprint


@full_database_exceptions
def get_a_secondary_fingerprint_of_client(db: Session, id_client: str) -> DbFingerprint:
    try:
        fingerprint = db.query(DbFingerprint).where(
            DbFingerprint.id_client == id_client,
            DbFingerprint.main_fingerprint == False,
            DbFingerprint.dropped == False
        ).first()
    except Exception as e:
        print(e)
        raise e

    if fingerprint is None:
        raise element_not_found_exception

    return fingerprint


@full_database_exceptions
def get_client_fingerprint_by_alias(
        db: Session,
        id_client: str,
        alias_fingerprint: str,
        mode: str = 'active'
) -> DbFingerprint:
    try:
        if mode == 'active':
            fingerprint = db.query(DbFingerprint).where(
                DbFingerprint.id_client == id_client,
                DbFingerprint.alias_fingerprint == alias_fingerprint,
                DbFingerprint.dropped == False
            ).one_or_none()
        elif mode == 'all':
            fingerprint = db.query(DbFingerprint).where(
                DbFingerprint.id_client == id_client,
                DbFingerprint.alias_fingerprint == alias_fingerprint
            ).first()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if fingerprint is None:
        raise element_not_found_exception

    return fingerprint


@multiple_attempts
@full_database_exceptions
def update_fingerprint(
        db: Session,
        request: FingerprintRequest,
        id_fingerprint: str,
        execute: str = 'now'
) -> DbFingerprint:
    updated_fingerprint = get_fingerprint_by_id(db, id_fingerprint)

    if updated_fingerprint.alias_fingerprint != request.alias_fingerprint:
        change_alias_fingerprint(
            db=db,
            id_client=updated_fingerprint.id_client,
            id_fingerprint=updated_fingerprint.id_fingerprint,
            alias_fingerprint=request.alias_fingerprint,
            execute='wait'
        )

    if request.main_fingerprint:
        change_main_fingerprint(
            db=db,
            change_main_to=request.main_fingerprint,
            new_main_fingerprint=updated_fingerprint,
            execute='wait'
        )

    updated_fingerprint.url_fingerprint = request.url_fingerprint
    updated_fingerprint.fingerprint_type = request.fingerprint_type.value
    updated_fingerprint.quality = request.quality.value
    updated_fingerprint.spectral_index = request.spectral_index
    updated_fingerprint.spatial_index = request.spatial_index

    try:
        if execute == 'now':
            db.commit()
            db.refresh(updated_fingerprint)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return updated_fingerprint


@multiple_attempts
@full_database_exceptions
def light_update(
        db: Session,
        request: FingerprintUpdateRequest,
        id_fingerprint: Optional[str] = None,
        fingerprint_object: Optional[DbFingerprint] = None,
        execute: str = 'now'
) -> DbFingerprint:

    if fingerprint_object is None:
        if id_fingerprint is None:
            raise element_not_found_exception
        fingerprint = get_fingerprint_by_id(db, id_fingerprint)
    else:
        fingerprint = fingerprint_object

    if fingerprint.alias_fingerprint != request.alias_fingerprint:
        change_alias_fingerprint(
            db=db,
            id_client=fingerprint.id_client,
            id_fingerprint=fingerprint.id_fingerprint,
            alias_fingerprint=request.alias_fingerprint,
            execute='wait'
        )

    if request.main_fingerprint:
        change_main_fingerprint(
            db=db,
            change_main_to=request.main_fingerprint,
            new_main_fingerprint=fingerprint,
            execute='wait'
        )

    try:
        if execute == 'now':
            db.commit()
            db.refresh(fingerprint)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return fingerprint


@multiple_attempts
@full_database_exceptions
def change_main_fingerprint(
        db: Session,
        change_main_to: bool,
        id_new_main_fingerprint: Optional[str] = None,
        new_main_fingerprint: Optional[DbFingerprint] = None,
        execute: str = 'now'
) -> bool:

    if new_main_fingerprint is None:
        if id_new_main_fingerprint is None:
            raise element_not_found_exception
        fingerprint = get_fingerprint_by_id(db, id_new_main_fingerprint)
    else:
        fingerprint = new_main_fingerprint

    if change_main_to:
        if not fingerprint.main_fingerprint:
            past_main_fingerprint = get_main_fingerprint_of_client(db, fingerprint.id_client)
            past_main_fingerprint.main_fingerprint = False
            fingerprint.main_fingerprint = True
    else:
        if fingerprint.main_fingerprint:
            raise not_main_element_exception

    try:
        if execute == 'now':
            db.commit()
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return True


@multiple_attempts
@full_database_exceptions
def change_alias_fingerprint(
        db: Session,
        id_fingerprint: str,
        alias_fingerprint: str,
        id_client: Optional[str] = None,
        execute: str = 'now'
) -> bool:
    if id_client is None:
        fingerprint = get_fingerprint_by_id(db, id_fingerprint)
        id_client = fingerprint.id_client

    try:
        get_client_fingerprint_by_alias(db, id_client, alias_fingerprint)
    except NotFoundException:
        db.query(DbFingerprint).where(
            DbFingerprint.id_fingerprint == id_fingerprint,
            DbFingerprint.dropped == False
        ).update(
            {DbFingerprint.alias_fingerprint: alias_fingerprint},
            synchronize_session=False
        )

        if execute == 'now':
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                print(e)
                raise e
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    else:
        raise not_unique_alias_exception

    return True


@multiple_attempts
@full_database_exceptions
def delete_fingerprint(db: Session, id_fingerprint: str, execute: str = 'now') -> BasicResponse:
    fingerprint = get_fingerprint_by_id(db, id_fingerprint)
    if fingerprint.main_fingerprint:
        try:
            new_main_fingerprint = get_a_secondary_fingerprint_of_client(db, fingerprint.id_client)
            new_main_fingerprint.main_fingerprint = True
        except NotFoundException:
            raise not_main_element_exception

    fingerprint.main_fingerprint = False
    fingerprint.dropped = True

    try:
        if execute == 'now':
            db.commit()
            db.refresh(fingerprint)
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return BasicResponse(
        operation="delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_fingerprints_by_id_client(db: Session, id_client: str, execute: str = 'now') -> BasicResponse:
    client = get_client_by_id_client(db, id_client, mode='all')
    if not client.dropped:
        # It is necessary that the client is erased to drop all associated fingerprints
        raise operation_need_a_precondition_exception

    fingerprints = get_fingerprints_by_id_client(db, id_client)
    for fingerprint in fingerprints:
        fingerprint.main_fingerprint = False
        fingerprint.dropped = True

    if execute == 'now':
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return BasicResponse(
        operation="Batch delete",
        successful=True
    )










