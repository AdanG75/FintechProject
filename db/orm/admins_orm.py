from typing import Optional, List
import uuid

from sqlalchemy.orm import Session

from db.orm.exceptions_orm import db_exception, element_not_found_exception
from db.orm.functions_orm import multiple_attempts
from schemas.admin_base import AdminRequest
from db.models.admins_db import DbAdmin
from schemas.basic_response import BasicResponse


@multiple_attempts
def create_admin(db: Session, request: AdminRequest) -> DbAdmin:
    admin_uuid = uuid.uuid4().hex
    id_admin = "SSS-" + admin_uuid

    new_admin = DbAdmin(
        id_admin=id_admin,
        id_user=request.id_user,
        full_name=request.full_name
    )

    try:
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
    except Exception as e:
        db.rollback()
        raise db_exception

    return new_admin


def get_admin_by_id_admin(db: Session, id_admin: str) -> Optional[DbAdmin]:
    try:
        admin = db.query(DbAdmin).where(
            DbAdmin.id_admin == id_admin
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if admin is None:
        raise element_not_found_exception

    return admin


def get_admin_by_id_user(db: Session, id_user: int) -> Optional[DbAdmin]:
    try:
        admin = db.query(DbAdmin).where(
            DbAdmin.id_user == id_user
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if admin is None:
        raise element_not_found_exception

    return admin


def get_all_admins(db: Session) -> Optional[List[DbAdmin]]:
    admins: Optional[List[DbAdmin]] = db.query(DbAdmin).all()

    return admins


@multiple_attempts
def update_admin(db: Session, request: AdminRequest, id_admin: str) -> DbAdmin:
    updated_admin = get_admin_by_id_admin(db, id_admin)

    updated_admin.full_name = request.full_name

    try:
        # Commit all changes
        db.commit()
        db.refresh(updated_admin)
    except Exception:
        db.rollback()
        raise db_exception

    return updated_admin


@multiple_attempts
def delete_admin(db: Session, id_admin: str) -> BasicResponse:
    admin = get_admin_by_id_admin(db, id_admin)

    if admin is not None:
        try:
            db.delete(admin)
            db.commit()
        except Exception:
            db.rollback()
            raise db_exception

    else:
        raise element_not_found_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
