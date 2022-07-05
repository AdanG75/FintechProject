from typing import List

from sqlalchemy.orm import Session

from db.models.minutiae_db import DbMinutiae
from db.orm.exceptions_orm import db_exception, element_not_found_exception, not_values_sent_exception
from db.orm.functions_orm import multiple_attempts
from fingerprint_process.models.minutia import Minutiae
from schemas.basic_response import BasicResponse


@multiple_attempts
def create_minutia(db: Session, request: Minutiae, id_fingerprint: str) -> bool:
    id_index = f"MNT-{request.get_minutiae_id()}"

    new_minutia = DbMinutiae(
        id_index=id_index,
        id_fingerprint=id_fingerprint,
        pos_x=request.get_posx(),
        pos_y=request.get_posy(),
        angle=round(request.get_angle(), 2),
        type=request.get_point_type()
    )

    try:
        db.add(new_minutia)
        db.commit()
        db.refresh(new_minutia)
    except Exception as e:
        db.rollback()
        raise db_exception

    return True


@multiple_attempts
def insert_list_of_minutiae(db: Session, minutiae: List[Minutiae], id_fingerprint: str) -> bool:
    if minutiae is None or len(minutiae) < 1:
        raise not_values_sent_exception

    try:
        for minutia in minutiae:
            id_index = f"MNT-{minutia.get_minutiae_id()}"
            minutia_to_insert = DbMinutiae(
                id_index=id_index,
                id_fingerprint=id_fingerprint,
                pos_x=minutia.get_posx(),
                pos_y=minutia.get_posy(),
                angle=round(minutia.get_angle(), 2),
                type=minutia.get_point_type()
            )
            db.add(minutia_to_insert)
    except Exception:
        db.rollback()
        raise db_exception
    else:
        db.commit()

    return True


def get_minutia_by_id(db: Session, id_index: str) -> DbMinutiae:
    try:
        minutia = db.query(DbMinutiae).where(
            DbMinutiae.id_minutia == id_index
        ).first()
    except Exception as e:
        raise db_exception

    if minutia is None:
        raise element_not_found_exception

    return minutia


def get_minutiae_by_id_fingerprint(db: Session, id_fingerprint: str) -> List[DbMinutiae]:
    try:
        minutiae = db.query(DbMinutiae).where(
            DbMinutiae.id_fingerprint == id_fingerprint
        ).all()
    except Exception as e:
        raise db_exception

    if minutiae is None or len(minutiae) < 1:
        raise element_not_found_exception

    return minutiae


@multiple_attempts
def delete_minutia(db: Session, id_index: str) -> BasicResponse:
    minutia = get_minutia_by_id(db, id_index)

    try:
        db.delete(minutia)
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
