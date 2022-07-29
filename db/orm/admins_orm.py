from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from db.orm.exceptions_orm import element_not_found_exception, type_of_value_not_compatible, option_not_found_exception, \
    NotFoundException, not_unique_value, operation_need_a_precondition_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from db.orm.users_orm import get_user_by_id
from schemas.admin_base import AdminRequest
from db.models.admins_db import DbAdmin
from db.models.users_db import DbUser
from schemas.basic_response import BasicResponse


@multiple_attempts
@full_database_exceptions
def create_admin(
        db: Session,
        request: AdminRequest,
        execute: str = 'now'
) -> DbAdmin:
    user: Optional[DbUser] = get_user_by_id(db, request.id_user)
    if user.type_user != 'admin':
        raise type_of_value_not_compatible

    # Clear user object to save space
    user = None

    try:
        admin = get_admin_by_id_user(db, request.id_user, mode='all')
    except NotFoundException:
        admin_uuid = uuid.uuid4().hex
        id_admin = "ADM-" + admin_uuid

        new_admin = DbAdmin(
            id_admin=id_admin,
            id_user=request.id_user,
            full_name=request.full_name,
            dropped=False
        )

        try:
            db.add(new_admin)
            if execute == 'now':
                db.commit()
                db.refresh(new_admin)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_admin

    if admin.dropped:
        return update_admin(db, request, admin.id_admin, mode='all', execute=execute)

    raise not_unique_value


@full_database_exceptions
def get_admin_by_id_admin(
        db: Session,
        id_admin: str,
        mode: str = 'active'
) -> DbAdmin:
    try:
        if mode == 'active':
            admin = db.query(DbAdmin).where(
                DbAdmin.id_admin == id_admin,
                DbAdmin.dropped == False
            ).one_or_none()
        elif mode == 'all':
            admin = db.query(DbAdmin).where(
                DbAdmin.id_admin == id_admin
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if admin is None:
        raise element_not_found_exception

    return admin


@full_database_exceptions
def get_admin_by_id_user(
        db: Session,
        id_user: int,
        mode: str = 'active'
) -> DbAdmin:
    try:
        if mode == 'active':
            admin = db.query(DbAdmin).where(
                DbAdmin.id_user == id_user,
                DbAdmin.dropped == False
            ).one_or_none()
        elif mode == 'all':
            admin = db.query(DbAdmin).where(
                DbAdmin.id_user == id_user
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if admin is None:
        raise element_not_found_exception

    return admin


@full_database_exceptions
def get_all_admins(db: Session) -> Optional[List[DbAdmin]]:
    try:
        admins: List[DbAdmin] = db.query(DbAdmin.dropped == False).all()
    except Exception as e:
        print(e)
        raise e

    return admins


@multiple_attempts
@full_database_exceptions
def update_admin(
        db: Session,
        request: AdminRequest,
        id_admin: str,
        mode: str = 'active',
        execute: str = 'now'
) -> DbAdmin:
    updated_admin = get_admin_by_id_admin(db, id_admin, mode=mode)

    updated_admin.full_name = request.full_name
    updated_admin.dropped = False

    if execute == 'now':
        try:
            # Commit all changes
            db.commit()
            db.refresh(updated_admin)
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return updated_admin


@multiple_attempts
@full_database_exceptions
def delete_admin(db: Session, id_admin: str, execute: str = 'now') -> BasicResponse:
    admin = get_admin_by_id_admin(db, id_admin)
    try:
        get_user_by_id(db, admin.id_user)
    except NotFoundException:
        # If user was not found that means it was deleted
        pass
    else:
        # It is necessary that the user is erased to drop the admin.
        raise operation_need_a_precondition_exception

    admin.dropped = True

    if execute == 'now':
        try:
            # No longer necessary
            # db.delete(admin)
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
        operation="delete",
        successful=True
    )
