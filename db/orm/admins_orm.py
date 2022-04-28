from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from starlette import status

from db.database import get_db
from schemas.admin_base import AdminRequest
from db.models.admins_db import DbAdmin
from core.hash import Hash
from core import token_functions

admin_oauth2_schema = OAuth2PasswordBearer(tokenUrl="/admin/login")

db_exception = HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't connect to the Database"
        )

admin_not_found_exception = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin's username not found"
        )

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Couldn't validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )


def create_admin(db: Session, request: AdminRequest):

    new_admin = DbAdmin(
        username=request.username,
        email=request.email,
        password=Hash.bcrypt(request.password)
    )
    try:
        # Add an insert request
        db.add(new_admin)
        # Commit all the request (in this case, only the insert request)
        db.commit()
        # Update "new_user" with the information of the column created
        db.refresh(new_admin)
    except Exception as e:
        raise db_exception

    return new_admin


def get_admin(db: Session, username: str) -> Optional[DbAdmin]:

    try:
        admin = db.query(DbAdmin).where(DbAdmin.username == username).first()
    except Exception as e:
        raise db_exception

    if admin is None:
        raise admin_not_found_exception

    return admin


def update_admin(db: Session, request: AdminRequest, username: str):
    admin = get_admin(db=db, username=username)

    if admin is not None:
        if len(request.email) < 80:
            admin.email = request.email
        else:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Email is too large, maximum length: 79 characters"
            )
        admin.username = request.username
        admin.password = Hash.bcrypt(request.password)

        try:
            # Commit all changes
            db.commit()
        except Exception:
            raise db_exception

    else:
        raise admin_not_found_exception

    return admin


def delete_admin(db: Session, username: str) -> dict:
    admin = get_admin(db=db, username=username)

    if admin is not None:
        try:
            db.delete(admin)
            db.commit()
        except Exception:
            raise db_exception

    else:
        raise admin_not_found_exception

    return {
        "operation": "delete",
        "successful": True
    }


def get_current_admin(db: Session = Depends(get_db),  token: str = Depends(admin_oauth2_schema)) -> DbAdmin:
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

        curr_dt = datetime.utcnow()
        timestamp = int(round(curr_dt.timestamp()))

        if timestamp < exp_time:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Token has expired"
            )

    except JWTError:
        raise credentials_exception

    admin: Optional[DbAdmin] = get_admin(db=db, username=admin_username)

    if admin is None:
        raise admin_not_found_exception

    return admin
