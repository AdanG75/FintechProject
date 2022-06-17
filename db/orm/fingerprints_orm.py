from typing import List
import uuid

from sqlalchemy.orm import Session

from db.models.fingerprints_db import DbFingerprint
from db.orm.exceptions_orm import db_exception, element_not_found_exception, \
    not_unique_alias_exception, not_main_element_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.fingerprint_base import FingerprintRequest, FingerprintUpdateRequest


@multiple_attempts
def create_fingerprint(db: Session, request: FingerprintRequest) -> DbFingerprint:
    fingerprint_uuid = uuid.uuid4().hex
    id_fingerprint = f"FNP-{fingerprint_uuid}"

    new_fingerprint = DbFingerprint(
        id_fingerprint=id_fingerprint,
        id_client=request.id_client,
        alias_fingerprint=request.alias_fingerprint,
        url_fingerprint=request.url_fingerprint,
        fingerprint_type=request.fingerprint_type,
        quality=request.quality,
        spectral_index=request.spectral_index,
        spatial_index=request.spatial_index,
        main_fingerprint=request.main_fingerprint
    )

    try:
        db.add(new_fingerprint)
        db.commit()
        db.refresh(new_fingerprint)
    except Exception as e:
        db.rollback()
        raise db_exception

    return new_fingerprint


@multiple_attempts
def add_fingerprint(db: Session, request: FingerprintRequest) -> DbFingerprint:
    added_fingerprint = create_fingerprint(db, request)

    if added_fingerprint.main_fingerprint:
        change_main_fingerprint(db, added_fingerprint.id_client, added_fingerprint.id_fingerprint)
        db.refresh(added_fingerprint)

    return added_fingerprint


def get_fingerprint_by_id(db: Session, id_fingerprint: str) -> DbFingerprint:
    try:
        fingerprint = db.query(DbFingerprint).where(
            DbFingerprint.id_fingerprint == id_fingerprint,
            DbFingerprint.dropped == False
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if fingerprint is None:
        raise element_not_found_exception

    return fingerprint


def get_fingerprints_by_id_client(db: Session, id_client: str) -> List[DbFingerprint]:
    try:
        fingerprints = db.query(DbFingerprint).where(
            DbFingerprint.id_client == id_client,
            DbFingerprint.dropped == False
        ).all()
    except Exception as e:
        raise db_exception

    if fingerprints is None:
        raise element_not_found_exception

    return fingerprints


def get_main_fingerprint_of_client(db: Session, id_client: str) -> DbFingerprint:
    try:
        fingerprint = db.query(DbFingerprint).where(
            DbFingerprint.id_client == id_client,
            DbFingerprint.main_fingerprint == True,
            DbFingerprint.dropped == False
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if fingerprint is None:
        raise element_not_found_exception

    return fingerprint


def get_client_fingerprint_by_alias(db: Session, id_client: str, alias_fingerprint: str) -> DbFingerprint:
    try:
        fingerprint = db.query(DbFingerprint).where(
            DbFingerprint.id_client == id_client,
            DbFingerprint.alias_fingerprint == alias_fingerprint,
            DbFingerprint.dropped == False
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if fingerprint is None:
        raise element_not_found_exception

    return fingerprint


@multiple_attempts
def update_fingerprint(db: Session, request: FingerprintRequest, id_fingerprint: str) -> DbFingerprint:
    updated_fingerprint = get_fingerprint_by_id(db, id_fingerprint)

    updated_fingerprint.url_fingerprint = request.url_fingerprint
    updated_fingerprint.fingerprint_type = request.fingerprint_type
    updated_fingerprint.quality = request.quality
    updated_fingerprint.spectral_index = request.spectral_index
    updated_fingerprint.spatial_index = request.spatial_index

    try:
        if updated_fingerprint.main_fingerprint:
            change_main_fingerprint(db, updated_fingerprint.id_client, updated_fingerprint.id_fingerprint)

        if updated_fingerprint.alias_fingerprint != request.alias_fingerprint:
            change_alias_fingerprint(
                db,
                updated_fingerprint.id_client,
                updated_fingerprint.id_fingerprint,
                request.alias_fingerprint
            )

        db.commit()
        db.refresh(updated_fingerprint)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_fingerprint


@multiple_attempts
def light_update(db: Session, request: FingerprintUpdateRequest) -> DbFingerprint:
    fingerprint = get_fingerprint_by_id(db, request.id_fingerprint)

    if fingerprint.main_fingerprint != request.main_fingerprint and not fingerprint.main_fingerprint:
        change_main_fingerprint(db, fingerprint.id_client, fingerprint.id_fingerprint)
    else:
        raise not_main_element_exception

    if fingerprint.alias_fingerprint != request.alias_fingerprint:
        change_alias_fingerprint(
            db=db,
            id_client=fingerprint.id_client,
            id_fingerprint=fingerprint.id_fingerprint,
            alias_fingerprint=request.alias_fingerprint
        )

    try:
        db.refresh(fingerprint)
    except Exception as e:
        db.rollback()
        raise db_exception

    return fingerprint


def change_main_fingerprint(db: Session, id_client: str, id_fingerprint: str) -> bool:
    try:
        db.query(DbFingerprint).where(
            DbFingerprint.id_fingerprint != id_fingerprint,
            DbFingerprint.id_client == id_client,
            DbFingerprint.dropped == False
        ).update(
            {DbFingerprint.main_fingerprint: False},
            synchronize_session=False
        )
        db.query(DbFingerprint).where(
            DbFingerprint.id_fingerprint == id_fingerprint,
            DbFingerprint.dropped == False
        ).update(
            {DbFingerprint.main_fingerprint: True},
            synchronize_session=False
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return True


def change_alias_fingerprint(
        db: Session,
        id_client: str,
        id_fingerprint: str,
        alias_fingerprint: str
) -> bool:
    try:
        get_client_fingerprint_by_alias(db, id_client, alias_fingerprint)
    except element_not_found_exception:
        db.query(DbFingerprint).where(
            DbFingerprint.id_fingerprint == id_fingerprint,
            DbFingerprint.dropped == False
        ).update(
            {DbFingerprint.alias_fingerprint: alias_fingerprint},
            synchronize_session=False
        )

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise db_exception
    else:
        raise not_unique_alias_exception

    return True


@multiple_attempts
def delete_fingerprint(db: Session, id_fingerprint: str) -> BasicResponse:
    fingerprint = get_fingerprint_by_id(db, id_fingerprint)
    fingerprint.dropped = True

    try:
        db.commit()
        db.refresh(fingerprint)
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )











