from typing import Optional, List

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth.token_functions import is_token_expired
from db.database import get_db
from db.orm.exceptions_orm import db_exception, element_not_found_exception, credentials_exception, \
    email_exception, not_unique_email_or_username_exception, not_unique_username_exception, not_unique_email_exception
from db.orm.functions_orm import multiple_attempts
from schemas.admin_base import AdminRequest
from db.models.admins_db import DbAdmin
from secure.hash import Hash
from auth import token_functions

admin_oauth2_schema = OAuth2PasswordBearer(tokenUrl="/admin/login")


@multiple_attempts
def create_admin(db: Session, request: AdminRequest):
    if len(request.email) >= 80:
        raise email_exception

    try:
        admin = get_admin_by_email_or_username(db, request.email, request.username)
    except element_not_found_exception:
        new_admin = DbAdmin(
            username=request.username,
            email=request.email,
            password=Hash.bcrypt(request.password),
            public_key=request.public_key
        )
        try:
            # Add an insert request
            db.add(new_admin)
            # Commit all the request (in this case, only the insert request)
            db.commit()
            # Update "new_user" with the information of the column created
            db.refresh(new_admin)
        except Exception as e:
            db.rollback()
            raise db_exception

        return new_admin

    raise not_unique_email_or_username_exception


def get_admin_by_username(db: Session, username: str) -> Optional[DbAdmin]:
    try:
        admin = db.query(DbAdmin).where(DbAdmin.username == username).one_or_none()
    except Exception as e:
        raise db_exception

    if admin is None:
        raise element_not_found_exception

    return admin


def get_admin_by_email(db: Session, email: str) -> Optional[DbAdmin]:
    try:
        admin = db.query(DbAdmin).where(DbAdmin.email == email).one_or_none()
    except Exception as e:
        raise db_exception

    if admin is None:
        raise element_not_found_exception

    return admin


def get_admin_by_email_or_username(db: Session, email: str, username: str) -> Optional[DbAdmin]:
    try:
        admin = db.query(DbAdmin).where(or_(
            DbAdmin.username == username,
            DbAdmin.email == email
        )).first()
    except Exception as e:
        raise db_exception

    if admin is None:
        raise element_not_found_exception

    return admin


def get_admin_by_id(id_admin: int, db: Session) -> Optional[DbAdmin]:
    try:
        admin = db.query(DbAdmin).where(DbAdmin.id == id_admin).one_or_none()
    except Exception as e:
        raise db_exception

    if admin is None:
        raise element_not_found_exception

    return admin


def get_public_key_pem(id_admin: int, db: Session) -> Optional[str]:
    admin: DbAdmin = get_admin_by_id(id_admin=id_admin, db=db)
    public_key_pem: Optional[str] = admin.public_key

    return public_key_pem


def get_all_admins(db: Session) -> Optional[List[DbAdmin]]:
    admins: Optional[List[DbAdmin]] = db.query(DbAdmin).all()

    return admins


@multiple_attempts
def update_admin(db: Session, request: AdminRequest, username: str):
    admin = get_admin_by_username(db=db, username=username)

    if admin is not None:
        if admin.username != request.username:
            try:
                get_admin_by_username(db, request.username)
            except element_not_found_exception:
                admin.username = request.username
            else:
                raise not_unique_username_exception

        if admin.email != request.email:
            try:
                get_admin_by_email(db, request.email)
            except element_not_found_exception:
                if len(request.email) < 80:
                    admin.email = request.email
                else:
                    raise email_exception
            else:
                raise not_unique_email_exception

        admin.password = Hash.bcrypt(request.password)
        admin.public_key = request.public_key

        try:
            # Commit all changes
            db.commit()
            db.refresh(admin)
        except Exception:
            db.rollback()
            raise db_exception

    else:
        raise element_not_found_exception

    return admin


@multiple_attempts
def delete_admin(db: Session, username: str) -> dict:
    admin = get_admin_by_username(db=db, username=username)

    if admin is not None:
        try:
            db.delete(admin)
            db.commit()
        except Exception:
            db.rollback()
            raise db_exception

    else:
        raise element_not_found_exception

    return {
        "operation": "delete",
        "successful": True
    }


def get_current_admin(db: Session = Depends(get_db), token: str = Depends(admin_oauth2_schema)) -> DbAdmin:
    try:
        payload = jwt.decode(
            token=token,
            key=token_functions.SECRET_KEY,
            algorithms=[token_functions.ALGORITHM]
        )
        admin_username: Optional[str] = payload.get("username")

        if admin_username is None:
            raise credentials_exception

        exp_time = payload.get("exp")
    except JWTError:
        raise credentials_exception

    if not is_token_expired(exp_time):
        admin: Optional[DbAdmin] = get_admin_by_username(db=db, username=admin_username)
        if admin is None:
            raise element_not_found_exception

        return admin

    raise credentials_exception
