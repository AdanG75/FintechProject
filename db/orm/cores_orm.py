from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models.cores_db import DbCores
from db.orm.exceptions_orm import element_not_found_exception, not_values_sent_exception, \
    option_not_found_exception, operation_need_a_precondition_exception
from db.orm.fingerprints_orm import get_fingerprint_by_id
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from fingerprint_process.models.core_point import CorePoint
from schemas.basic_response import BasicResponse


@multiple_attempts
@full_database_exceptions
def create_core_point(
        db: Session,
        request: CorePoint,
        id_fingerprint: str,
        execute: str = 'now'
) -> bool:
    id_core = f"COR-{request.get_minutiae_id()}"

    new_core_point = DbCores(
        id_core=id_core,
        id_fingerprint=id_fingerprint,
        pos_x=request.get_posx(),
        pos_y=request.get_posy(),
        angle=round(request.get_angle(), 2),
        type_core=request.get_point_type()
    )

    try:
        db.add(new_core_point)
        if execute == 'now':
            db.commit()
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except HTTPException as httpe:
        db.rollback()
        raise httpe
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return True


@multiple_attempts
@full_database_exceptions
def insert_list_of_core_points(
        db: Session,
        core_points: List[CorePoint],
        id_fingerprint: str,
        execute: str = 'now'
) -> bool:
    if core_points is None or len(core_points) < 1:
        raise not_values_sent_exception

    try:
        for core_point in core_points:
            create_core_point(db, core_point, id_fingerprint, execute='wait')

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
def get_core_point_by_id(db: Session, id_core: str) -> DbCores:
    try:
        core_point = db.query(DbCores).where(
            DbCores.id_core == id_core
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if core_point is None:
        raise element_not_found_exception

    return core_point


@multiple_attempts
@full_database_exceptions
def get_core_points_by_id_fingerprint(db: Session, id_fingerprint: str) -> List[DbCores]:
    try:
        core_points = db.query(DbCores).where(
            DbCores.id_fingerprint == id_fingerprint
        ).all()
    except Exception as e:
        print(e)
        raise e

    if core_points is None or len(core_points) < 1:
        raise element_not_found_exception

    return core_points


@multiple_attempts
@full_database_exceptions
def delete_core_point(
        db: Session,
        id_core: Optional[str] = None,
        core_object: Optional[DbCores] = None,
        execute: str = 'now'
) -> BasicResponse:
    if core_object is None:
        if id_core is not None:
            core_object = get_core_point_by_id(db, id_core)
        else:
            raise not_values_sent_exception

    try:
        db.delete(core_object)
        if execute == 'now':
            db.commit()
        elif execute == 'wait':
            pass
        else:
            raise option_not_found_exception
    except HTTPException as httpe:
        db.rollback()
        raise httpe
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
def delete_all_core_points_of_fingerprint(db: Session, id_fingerprint: str, execute: str = 'now') -> BasicResponse:
    fingerprint = get_fingerprint_by_id(db, id_fingerprint, mode='all')
    if not fingerprint.dropped:
        # It is necessary that fingerprint is erased to drop all associated core points
        raise operation_need_a_precondition_exception

    cores = get_core_points_by_id_fingerprint(db, id_fingerprint)
    for core in cores:
        delete_core_point(db=db, core_object=core, execute='wait')

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
