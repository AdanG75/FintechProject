from datetime import datetime

from sqlalchemy.orm import Session

from db.models.password_recoveries_db import DbPasswordRecovery
from db.orm.exceptions_orm import db_exception, element_not_found_exception, too_many_attempts_exception, \
    not_valid_operation_exception
from db.orm.functions_orm import multiple_attempts
from web_utils.web_functions import generate_code, set_expiration_time


@multiple_attempts
def create_code_to_recover_password(db: Session, id_user: int) -> DbPasswordRecovery:
    password_recovery = get_password_recovery_by_id_user(db, id_user)

    password_recovery.code = generate_code()
    password_recovery.expiration_time = set_expiration_time(minutes=20)
    password_recovery.attempts = 0
    password_recovery.is_valid = True

    try:
        db.commit()
        db.refresh(password_recovery)
    except Exception as e:
        db.rollback()
        raise db_exception

    return password_recovery


def get_password_recovery_by_id_recover(db: Session, id_recover: int) -> DbPasswordRecovery:
    try:
        password_recovery = db.query(DbPasswordRecovery).where(
            DbPasswordRecovery.id_recover == id_recover
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if password_recovery is None:
        raise element_not_found_exception

    return password_recovery


def get_password_recovery_by_id_user(db: Session, id_user: int) -> DbPasswordRecovery:
    try:
        password_recovery = db.query(DbPasswordRecovery).where(
            DbPasswordRecovery.id_user == id_user
        ).one_or_none()
    except Exception as e:
        raise db_exception

    if password_recovery is None:
        raise element_not_found_exception

    return password_recovery


def check_code_of_password_recovery(db: Session, id_user: int, code: int) -> bool:
    password_recovery = get_password_recovery_by_id_user(db, id_user)

    if not password_recovery.is_valid:
        raise not_valid_operation_exception

    if password_recovery.expiration_time is None or password_recovery.expiration_time < datetime.utcnow():
        invalid_password_recovery(db, password_recovery)
        raise not_valid_operation_exception

    if password_recovery.code == code:
        invalid_password_recovery(db, password_recovery)
        return True
    else:
        add_attempt(db, password_recovery)
        return False


@multiple_attempts
def add_attempt(db: Session, password_recovery: DbPasswordRecovery) -> bool:

    if password_recovery.attempts < 5:
        password_recovery.attempts += 1
    else:
        invalid_password_recovery(db, password_recovery)
        raise too_many_attempts_exception

    try:
        db.commit()
        db.refresh(password_recovery)
    except Exception as e:
        db.rollback()
        raise db_exception

    return True


@multiple_attempts
def invalid_password_recovery(db: Session, password_recovery: DbPasswordRecovery) -> bool:

    password_recovery.is_valid = False
    password_recovery.code = None
    password_recovery.expiration_time = None

    try:
        db.commit()
        db.refresh(password_recovery)
    except Exception as e:
        db.rollback()
        raise db_exception

    return True


