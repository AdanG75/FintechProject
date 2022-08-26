from typing import List, Optional

from sqlalchemy.orm import Session

from db.models.minutiae_db import DbMinutiae
from db.orm.exceptions_orm import element_not_found_exception, not_values_sent_exception, \
    option_not_found_exception, operation_need_a_precondition_exception
from db.orm.fingerprints_orm import get_fingerprint_by_id
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from fingerprint_process.models.minutia import Minutiae
from schemas.basic_response import BasicResponse


@multiple_attempts
@full_database_exceptions
def create_minutia(
        db: Session,
        request: Minutiae,
        id_fingerprint: str,
        execute: str = 'now'
) -> bool:
    id_minutia = f"MNT-{request.get_minutiae_id()}"

    new_minutia = DbMinutiae(
        id_minutia=id_minutia,
        id_fingerprint=id_fingerprint,
        pos_x=request.get_posx(),
        pos_y=request.get_posy(),
        angle=round(request.get_angle(), 2),
        type=request.get_point_type()
    )

    try:
        db.add(new_minutia)
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
def insert_list_of_minutiae(
        db: Session,
        minutiae: List[Minutiae],
        id_fingerprint: str,
        execute: str = 'now'
) -> bool:
    if minutiae is None or len(minutiae) < 1:
        raise not_values_sent_exception

    try:
        for minutia in minutiae:
            create_minutia(db, minutia, id_fingerprint, execute='wait')

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
    else:
        db.commit()

    return True


@multiple_attempts
@full_database_exceptions
def get_minutia_by_id(db: Session, id_minutia: str) -> DbMinutiae:
    try:
        minutia = db.query(DbMinutiae).where(
            DbMinutiae.id_minutia == id_minutia
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if minutia is None:
        raise element_not_found_exception

    return minutia


@multiple_attempts
@full_database_exceptions
def get_minutiae_by_id_fingerprint(db: Session, id_fingerprint: str) -> List[DbMinutiae]:
    try:
        minutiae = db.query(DbMinutiae).where(
            DbMinutiae.id_fingerprint == id_fingerprint
        ).all()
    except Exception as e:
        print(e)
        raise e

    if minutiae is None or len(minutiae) < 1:
        raise element_not_found_exception

    return minutiae


@multiple_attempts
@full_database_exceptions
def delete_minutia(
        db: Session,
        id_minutia: Optional[str] = None,
        minutia_object: Optional[DbMinutiae] = None,
        execute: str = 'now'
) -> BasicResponse:
    if minutia_object is None:
        if id_minutia is not None:
            minutia_object = get_minutia_by_id(db, id_minutia)
        else:
            raise not_values_sent_exception

    try:
        db.delete(minutia_object)
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

    return BasicResponse(
        operation="Delete",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_all_minutiae_of_fingerprint(db: Session, id_fingerprint: str, execute: str = 'naw') -> BasicResponse:
    fingerprint = get_fingerprint_by_id(db, id_fingerprint, mode='all')
    if not fingerprint.dropped:
        # It is necessary that fingerprint is erased to drop all associated core points
        raise operation_need_a_precondition_exception

    minutiae = get_minutiae_by_id_fingerprint(db, id_fingerprint)
    for minutia in minutiae:
        delete_minutia(db=db, minutia_object=minutia, execute='wait')

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

    return BasicResponse(
        operation="Batch delete",
        successful=True
    )
