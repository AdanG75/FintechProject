from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from core.utils import is_valid_phone_number, set_phone_number_format
from db.models.accounts_db import DbAccount  # Don't erase because it is used by relationship
from db.models.users_db import DbUser
from db.orm.exceptions_orm import email_exception, element_not_found_exception, \
    not_unique_email_exception, type_not_found_exception, phone_exception, option_not_found_exception, \
    NotFoundException, wrong_data_sent_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from schemas.basic_response import BasicResponse
from schemas.type_user import TypeUser
from schemas.user_base import UserRequest
from secure.hash import Hash


@multiple_attempts
@full_database_exceptions
def create_user(db: Session, request: UserRequest, execute: str = 'now') -> DbUser:
    if request.password is None:
        raise wrong_data_sent_exception

    if len(request.email) >= 80:
        raise email_exception

    if request.phone is not None:
        formatted_phone = set_phone_number_format(request.phone)
        if not is_valid_phone_number(formatted_phone):
            raise phone_exception
    else:
        formatted_phone = request.phone

    try:
        user = get_user_by_email(db, request.email, mode='all')
    except NotFoundException:
        new_user = DbUser(
            email=request.email,
            name=request.name,
            password=Hash.bcrypt(request.password),
            type_user=request.type_user.value,
            phone=formatted_phone,
            public_key=request.public_key,
            created_time=datetime.utcnow(),
            dropped=False
        )

        try:
            db.add(new_user)
            if execute == 'now':
                db.commit()
                db.refresh(new_user)
            elif execute == 'wait':
                pass
            else:
                raise option_not_found_exception
        except Exception as e:
            db.rollback()
            print(e)
            raise e

        return new_user

    if user.dropped:
        return update_user(db, request, user.id_user, mode='all', execute=execute)

    raise not_unique_email_exception


@full_database_exceptions
def get_user_by_id(db: Session, id_user: int, mode: str = 'active') -> DbUser:

    try:
        if mode == 'active':
            user = db.query(DbUser).where(
                DbUser.id_user == id_user,
                DbUser.dropped == False
            ).one_or_none()
        elif mode == 'all':
            user = db.query(DbUser).where(
                DbUser.id_user == id_user
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if user is None:
        raise element_not_found_exception

    return user


@full_database_exceptions
def get_user_by_email(db: Session, email: str, mode: str = 'active') -> DbUser:
    try:
        if mode == 'active':
            user = db.query(DbUser).where(
                DbUser.email == email,
                DbUser.dropped == False
            ).one_or_none()
        elif mode == 'all':
            user = db.query(DbUser).where(
                DbUser.email == email
            ).one_or_none()
        else:
            raise option_not_found_exception
    except Exception as e:
        print(e)
        raise e

    if user is None:
        raise element_not_found_exception

    return user


@full_database_exceptions
def get_users_by_type(db: Session, user_type: str) -> List[DbUser]:
    try:
        TypeUser(user_type)
    except ValueError:
        raise type_not_found_exception

    try:
        users = db.query(DbUser).where(
            DbUser.type_user == user_type,
            DbUser.dropped == False
        ).all()
    except Exception as e:
        print(e)
        raise e

    if users is None or len(users) < 1:
        raise element_not_found_exception

    return users


@full_database_exceptions
def get_all_users(db: Session) -> Optional[List[DbUser]]:
    try:
        all_users = db.query(DbUser).where(DbUser.dropped == False).all()
    except Exception as e:
        print(e)
        raise e

    return all_users


@full_database_exceptions
def get_public_key_pem(db: Session, id_user: int) -> Optional[str]:
    user = get_user_by_id(db, id_user)
    public_key_pem = user.public_key

    return public_key_pem


@multiple_attempts
@full_database_exceptions
def update_user(
        db: Session,
        request: UserRequest,
        id_user: int,
        mode: str = 'active',
        execute: str = 'now'
) -> DbUser:
    updated_user = get_user_by_id(db, id_user, mode=mode)

    if updated_user.email != request.email:
        try:
            get_user_by_email(db, request.email, mode='all')
        except NotFoundException:
            if len(request.email) < 80:
                updated_user.email = request.email
            else:
                raise email_exception
        else:
            raise not_unique_email_exception

    if request.phone is not None:
        formatted_phone = set_phone_number_format(request.phone)
        if not is_valid_phone_number(formatted_phone):
            raise phone_exception
    else:
        formatted_phone = request.phone

    if request.password is not None:
        updated_user.password = Hash.bcrypt(request.password)

    updated_user.name = request.name
    updated_user.phone = formatted_phone
    updated_user.public_key = request.public_key
    updated_user.dropped = False

    if execute == 'now':
        try:
            db.commit()
            db.refresh(updated_user)
        except Exception as e:
            db.rollback()
            print(e)
            raise e
    elif execute == 'wait':
        pass
    else:
        raise option_not_found_exception

    return updated_user


@multiple_attempts
@full_database_exceptions
def set_public_key(db: Session, id_user: int, public_key: str) -> BasicResponse:
    user = get_user_by_id(db, id_user)
    user.public_key = public_key

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return BasicResponse(
        operation="set element",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def set_new_password(
        db: Session,
        id_user: int,
        new_password: str,
        recover_user: bool = False
) -> BasicResponse:
    user = get_user_by_id(db, id_user)
    user.password = Hash.bcrypt(new_password)
    if recover_user:
        user.dropped = False

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return BasicResponse(
        operation="Change password",
        successful=True
    )


@multiple_attempts
@full_database_exceptions
def delete_user(db: Session, id_user: int, execute: str = 'now') -> BasicResponse:
    user = get_user_by_id(db, id_user)
    user.dropped = True

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
        operation="delete",
        successful=True
    )
