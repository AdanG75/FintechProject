from typing import List, Optional

from sqlalchemy.orm import Session

from db.models.users_db import DbUser
from db.orm.exceptions_orm import db_exception, email_exception, element_not_found_exception, \
    not_unique_email_exception, type_not_found_exception
from db.orm.functions_orm import multiple_attempts
from schemas.basic_response import BasicResponse
from schemas.type_user import TypeUser
from schemas.user_base import UserRequest
from secure.hash import Hash


@multiple_attempts
def create_user(db: Session, request: UserRequest) -> DbUser:
    if len(request.email) >= 80:
        raise email_exception

    try:
        user = get_user_by_email(db, request.email)
    except element_not_found_exception:
        new_user = DbUser(
            email=request.email,
            name=request.name,
            password=Hash.bcrypt(request.password),
            user_type=request.user_type.value,
            public_key=request.public_key
        )

        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        except Exception as e:
            db.rollback()
            raise db_exception

        return new_user

    raise not_unique_email_exception


def get_user_by_id(db: Session, id_user) -> DbUser:
    try:
        user = db.query(DbUser).where(
            DbUser.id_user == id_user,
            DbUser.dropped == False
        ).one_or_none()

    except Exception as e:
        raise db_exception

    if user is None:
        raise element_not_found_exception

    return user


def get_user_by_email(db: Session, email: str) -> DbUser:
    try:
        user = db.query(DbUser).where(
            DbUser.email == email,
            DbUser.dropped == False
        ).one_or_none()

    except Exception as e:
        raise db_exception

    if user is None:
        raise element_not_found_exception

    return user


def get_users_by_type(db: Session, user_type: str) -> List[DbUser]:
    try:
        TypeUser(user_type)
    except ValueError:
        raise type_not_found_exception

    users = db.query(DbUser).where(
        DbUser.type_user == user_type,
        DbUser.dropped == False
    ).all()

    if users is None or len(users) < 1:
        raise element_not_found_exception

    return users


def get_public_key_pem(db: Session, id_user) -> Optional[str]:
    user = get_user_by_id(db, id_user)
    public_key_pem = user.public_key

    return public_key_pem


@multiple_attempts
def update_user(db: Session, request: UserRequest, id_user: int) -> DbUser:
    updated_user = get_user_by_id(db, id_user)

    if updated_user.email != request.email:
        try:
            get_user_by_email(db, request.email)
        except element_not_found_exception:
            if len(request.email) < 80:
                updated_user.email = request.email
            else:
                raise email_exception
        else:
            raise not_unique_email_exception

    updated_user.type_user = request.user_type.value
    updated_user.name = request.name
    updated_user.password = Hash.bcrypt(request.password)
    updated_user.public_key = request.public_key

    try:
        db.commit()
        db.refresh(updated_user)
    except Exception as e:
        db.rollback()
        raise db_exception

    return updated_user


@multiple_attempts
def delete_user(db: Session, id_user: int) -> BasicResponse:
    user = get_user_by_id(db, id_user)
    user.dropped = True

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise db_exception

    return BasicResponse(
        operation="delete",
        successful=True
    )
