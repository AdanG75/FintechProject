from typing import List
import uuid

from sqlalchemy.orm import Session

from db.orm.exceptions_orm import element_not_found_exception, wrong_data_sent_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.admin_base import AdminRequest
from db.models.admins_db import DbAdmin
from db.models.users_db import DbUser
from schemas.basic_response import BasicResponse


@multiple_attempts
@full_database_exceptions
def create_admin(db: Session, request: AdminRequest) -> DbAdmin:
    user: DbUser = get_user_by_id(db, request.id_user)
    if user.type_user != 'admin':
        raise wrong_data_sent_exception

    admin_uuid = uuid.uuid4().hex
    id_admin = "ADM-" + admin_uuid

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
        print(e)
        raise e

    return new_admin


@full_database_exceptions
def get_admin_by_id_admin(db: Session, id_admin: str) -> DbAdmin:
    try:
        admin = db.query(DbAdmin).where(
            DbAdmin.id_admin == id_admin
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if admin is None:
        raise element_not_found_exception

    return admin


@full_database_exceptions
def get_admin_by_id_user(db: Session, id_user: int) -> DbAdmin:
    try:
        admin = db.query(DbAdmin).where(
            DbAdmin.id_user == id_user
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if admin is None:
        raise element_not_found_exception

    return admin


@full_database_exceptions
def get_all_admins(db: Session) -> List[DbAdmin]:
    try:
        admins: List[DbAdmin] = db.query(DbAdmin).all()
    except Exception as e:
        print(e)
        raise e

    return admins


@multiple_attempts
@full_database_exceptions
def update_admin(db: Session, request: AdminRequest, id_admin: str) -> DbAdmin:
    updated_admin = get_admin_by_id_admin(db, id_admin)

    updated_admin.full_name = request.full_name

    try:
        # Commit all changes
        db.commit()
        db.refresh(updated_admin)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return updated_admin


@multiple_attempts
@full_database_exceptions
def delete_admin(db: Session, id_admin: str) -> BasicResponse:
    admin = get_admin_by_id_admin(db, id_admin)

    try:
        db.delete(admin)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return BasicResponse(
        operation="delete",
        successful=True
    )
