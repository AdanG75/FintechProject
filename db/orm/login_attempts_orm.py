from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from db.models.login_attempts_db import DbLoginAttempt
from db.orm.exceptions_orm import element_not_found_exception, inactive_password_exception
from db.orm.functions_orm import multiple_attempts, full_database_exceptions
from web_utils.web_functions import set_expiration_time


def check_attempt(db: Session, id_user: int, raise_exception: bool = False) -> bool:
    login_attempt = get_login_attempt_by_id_user(db, id_user)

    if login_attempt.attempts < 5:
        return True
    elif login_attempt.attempts < 12:
        if login_attempt.next_attempt_time is not None:
            if login_attempt.next_attempt_time <= datetime.utcnow():
                return True
            else:
                if raise_exception:
                    date_str = login_attempt.next_attempt_time.__str__()
                    raise HTTPException(
                        status_code=status.HTTP_425_TOO_EARLY,
                        detail=f"You must try after of time: {date_str} (UTC)"
                    )

                return False
        else:
            raise inactive_password_exception
    elif login_attempt.attempts >= 12:
        raise inactive_password_exception
    else:
        if raise_exception:
            date_str = login_attempt.next_attempt_time.__str__()
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail=f"You must try after of time: {date_str} (UTC)"
            )

        return False


@full_database_exceptions
def get_login_attempt_by_id_user(db: Session, id_user: int) -> DbLoginAttempt:
    try:
        login_attempt = db.query(DbLoginAttempt).where(
            DbLoginAttempt.id_user == id_user
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if login_attempt is None:
        raise element_not_found_exception

    return login_attempt


@full_database_exceptions
def get_login_attempt_by_id_attempt(db: Session, id_attempt: int) -> DbLoginAttempt:
    try:
        login_attempt = db.query(DbLoginAttempt).where(
            DbLoginAttempt.id_attempt == id_attempt
        ).one_or_none()
    except Exception as e:
        print(e)
        raise e

    if login_attempt is None:
        raise element_not_found_exception

    return login_attempt


@multiple_attempts
@full_database_exceptions
def add_attempt(db: Session, id_user: int) -> DbLoginAttempt:
    login_attempt = get_login_attempt_by_id_user(db, id_user)

    if login_attempt.next_attempt_time is not None:
        if login_attempt.next_attempt_time > datetime.utcnow():
            date_str = login_attempt.next_attempt_time.__str__()
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail=f"You must try after of time: {date_str} (UTC)"
            )

    if login_attempt.attempts == 4:
        login_attempt.next_attempt_time = set_expiration_time(minutes=30)
    elif login_attempt.attempts == 7:
        login_attempt.next_attempt_time = set_expiration_time(minutes=120)
    elif login_attempt.attempts == 9:
        login_attempt.next_attempt_time = set_expiration_time(minutes=360)
    elif login_attempt.attempts == 10:
        login_attempt.next_attempt_time = set_expiration_time(minutes=720)
    elif login_attempt.attempts == 11:
        login_attempt.next_attempt_time = set_expiration_time(minutes=1440)
    elif login_attempt.attempts >= 12:
        raise inactive_password_exception
    else:
        pass

    login_attempt.attempts += 1

    try:
        db.commit()
        db.refresh(login_attempt)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return login_attempt


@multiple_attempts
@full_database_exceptions
def reset_login_attempt(db: Session, id_user: int) -> bool:
    login_attempt = get_login_attempt_by_id_user(db, id_user)

    login_attempt.attempts = 0
    login_attempt.next_attempt_time = None

    try:
        db.commit()
        db.refresh(login_attempt)
    except Exception as e:
        db.rollback()
        print(e)
        raise e

    return True
