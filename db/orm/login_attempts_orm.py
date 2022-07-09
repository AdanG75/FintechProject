from datetime import datetime

from sqlalchemy.orm import Session

from db.models.login_attempts_db import DbLoginAttempt
from db.orm.exceptions_orm import db_exception, element_not_found_exception, too_many_attempts_exception, \
    inactive_password_exception
from db.orm.functions_orm import multiple_attempts
from web_utils.web_functions import set_expiration_time


def check_attempt(db: Session, id_user: int) -> bool:
    login_attempt = get_login_attempt_by_id_user(db, id_user)

    if login_attempt.attempts < 5:
        return True
    elif login_attempt.attempts < 12 and login_attempt.next_attempt_time <= datetime.utcnow():
        return True
    elif login_attempt >= 12:
        raise inactive_password_exception
    else:
        return False


def get_login_attempt_by_id_user(db: Session, id_user: int) -> DbLoginAttempt:
    try:
        login_attempt = db.query(DbLoginAttempt).where(
            DbLoginAttempt.id_user == id_user
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if login_attempt is None:
        raise element_not_found_exception

    return login_attempt


def get_login_attempt_by_id_attempt(db: Session, id_attempt: int) -> DbLoginAttempt:
    try:
        login_attempt = db.query(DbLoginAttempt).where(
            DbLoginAttempt.id_attempt == id_attempt
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if login_attempt is None:
        raise element_not_found_exception

    return login_attempt


@multiple_attempts
def add_attempt(db: Session, id_user: int) -> DbLoginAttempt:
    login_attempt = get_login_attempt_by_id_user(db, id_user)

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
        raise db_exception

    return login_attempt


@multiple_attempts
def reset_login_attempt(db: Session, id_user: int) -> bool:
    login_attempt = get_login_attempt_by_id_user(db, id_user)

    login_attempt.attempts = 0
    login_attempt.next_attempt_time = None

    try:
        db.commit()
        db.refresh(login_attempt)
    except Exception as e:
        db.rollback()
        raise db_exception

    return True

