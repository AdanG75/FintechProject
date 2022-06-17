from typing import List

from sqlalchemy.orm import Session

from db.models.characteristic_points_db import DbCharacteristicPoint
from db.orm.exceptions_orm import db_exception, element_not_found_exception, not_values_sent_exception
from db.orm.functions_orm import multiple_attempts
from fingerprint_process.models.core_point import CorePoint
from schemas.basic_response import BasicResponse


@multiple_attempts
def create_core_point(db: Session, request: CorePoint, id_fingerprint: str) -> bool:
    id_characteristic = f"CHP-{request.get_minutiae_id()}"

    new_core_point = DbCharacteristicPoint(
        id_characteristic=id_characteristic,
        id_fingerprint=id_fingerprint,
        pos_x=request.get_posx(),
        pos_y=request.get_posy(),
        angle=round(request.get_angle(), 2),
        type=request.get_point_type()
    )

    try:
        db.add(new_core_point)
        db.commit()
        db.refresh(new_core_point)
    except Exception as e:
        db.rollback()
        raise db_exception

    return True


@multiple_attempts
def insert_list_of_core_points(db: Session, core_points: List[CorePoint], id_fingerprint: str) -> bool:
    if core_points is None or len(core_points) < 1:
        raise not_values_sent_exception

    try:
        for core_point in core_points:
            id_characteristic = f"CHP-{core_point.get_minutiae_id()}"
            core_point_to_insert = DbCharacteristicPoint(
                id_characteristic=id_characteristic,
                id_fingerprint=id_fingerprint,
                pos_x=core_point.get_posx(),
                pos_y=core_point.get_posy(),
                angle=round(core_point.get_angle(), 2),
                type=core_point.get_point_type()
            )
            db.add(core_point_to_insert)
    except Exception:
        db.rollback()
        raise db_exception
    else:
        db.commit()

    return True


def get_core_point_by_id(db: Session, id_characteristic: str) -> DbCharacteristicPoint:
    try:
        core_point = db.query(DbCharacteristicPoint).where(
            DbCharacteristicPoint.id_characteristic == id_characteristic
        ).first()
    except Exception as e:
        raise db_exception

    if core_point is None:
        raise element_not_found_exception

    return core_point


def get_core_points_by_id_fingerprint(db: Session, id_fingerprint: str) -> List[DbCharacteristicPoint]:
    try:
        core_points = db.query(DbCharacteristicPoint).where(
            DbCharacteristicPoint.id_fingerprint == id_fingerprint
        ).all()
    except Exception as e:
        raise db_exception

    if core_points is None or len(core_points) < 1:
        raise element_not_found_exception

    return core_points


@multiple_attempts
def delete_core_point(db: Session, id_characteristic) -> BasicResponse:
    core_point = get_core_point_by_id(db, id_characteristic)

    try:
        db.delete(core_point)
        db.commit()
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
