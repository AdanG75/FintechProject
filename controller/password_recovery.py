from http.client import HTTPException
from typing import Optional

from redis.client import Redis
from sqlalchemy.orm import Session

from core.cache import batch_save, check_item_if_exist, item_get, item_save
from core.logs import show_error_message
from core.utils import generate_random_string
from db.orm.exceptions_orm import NotFoundException, bad_email_exception, error_while_generating_code_exception, \
    error_while_checking_code_exception, too_many_attempts_exception, not_authorized_exception
from db.orm.password_recoveries_orm import create_code_to_recover_password, reset_password_recovery_by_id_user, \
    check_code_of_password_recovery, get_password_recovery_by_id_user, add_attempt
from db.orm.users_orm import get_user_by_email, set_new_password
from schemas.basic_response import CodeRequest, ChangePasswordRequest


def generate_new_code_to_recover_password(
        db: Session,
        user_email: str,
        r: Redis
) -> str:
    try:
        user = get_user_by_email(db, user_email)
    except NotFoundException:
        raise error_while_generating_code_exception

    try:
        code_object = create_code_to_recover_password(db, user.id_user)
    except Exception as e:
        show_error_message(e)
        raise error_while_generating_code_exception

    result = create_values_in_cache_to_recover(r, code_object.id_user, code_object.code)

    if not result:
        raise error_while_generating_code_exception

    return code_object.code


def create_values_in_cache_to_recover(
        r: Redis,
        user_id: int,
        code: str
) -> bool:

    password_recovery_values = {
        f'CODE-REC-{user_id}': code,
        f'ATMS-REC-{user_id}': 0
    }

    results = batch_save(r, password_recovery_values, seconds=3600)

    if results.count(False) > 0:
        return False

    return True


def create_confirmation_ticket_in_cache(r: Redis, id_user: int) -> str:
    ticket = generate_random_string(16)

    # The confirmation ticket will be saved during one hour
    item_save(r, f'CONF-REC-{id_user}', ticket, seconds=3600)

    return ticket


def check_ticket_from_cache(r: Redis, id_user: int, ticket: str) -> Optional[bool]:
    return check_item_if_exist(r, f'CONF-REC-{id_user}', ticket)


def check_code_in_cache(r: Redis, id_user: int, code: str) -> Optional[bool]:
    attempts = item_get(r, f'ATMS-REC-{id_user}')
    if attempts is None:
        return None
    else:
        if int(attempts) >= 5:
            raise too_many_attempts_exception

    result = check_item_if_exist(r, f'CODE-REC-{id_user}', code)

    # Ignore the hint message. We do a different process when the result is None, and when the result is False.
    if result is False:
        r.incr(f'ATMS-REC-{id_user}', 1)

    return result


def check_code_in_db(db: Session, id_user: int, code: str) -> bool:
    return check_code_of_password_recovery(db, id_user, code)


def add_attempt_in_db(db: Session, id_user: int) -> bool:
    try:
        password_recovery = get_password_recovery_by_id_user(db, id_user)
    except NotFoundException as e:
        show_error_message(e)
        raise error_while_checking_code_exception

    return add_attempt(db, password_recovery)


def check_code(db: Session, code_object: CodeRequest, r: Redis) -> Optional[str]:
    try:
        user = get_user_by_email(db, code_object.email)
    except NotFoundException:
        raise error_while_checking_code_exception

    try:
        result_cache = check_code_in_cache(r, user.id_user, code_object.code)
    except HTTPException as e:
        clean_password_recovery_request(db, id_user=user.id_user, r=r)
        raise e

    if result_cache is None:
        result_db = check_code_in_db(db, user.id_user, code_object.code)
        if result_db:
            clean_password_recovery_cache_values(r, user.id_user)
            ticket = create_confirmation_ticket_in_cache(r, user.id_user)
            return ticket

    elif result_cache:
        clean_password_recovery_request(db, id_user=user.id_user, r=r)
        ticket = create_confirmation_ticket_in_cache(r, user.id_user)
        return ticket

    else:
        add_attempt_in_db(db, user.id_user)

    return None


def change_password(db: Session, r: Redis, ticket_object: ChangePasswordRequest) -> bool:
    try:
        user = get_user_by_email(db, ticket_object.email)
    except NotFoundException:
        raise not_authorized_exception

    if check_ticket_from_cache(r, user.id_user, ticket_object.ticket):
        set_new_password(db, user.id_user, ticket_object.password)
        clean_confirmation_ticket(r, user.id_user)
    else:
        raise not_authorized_exception

    return True


def clean_password_recovery_cache_values(r: Redis, id_user: int) -> Optional[int]:
    return r.delete(f'CODE-REC-{id_user}', f'ATMS-REC-{id_user}')


def clean_password_recovery_db(db: Session, id_user: int) -> bool:
    return reset_password_recovery_by_id_user(db, id_user)


def clean_confirmation_ticket(r: Redis, id_user: int) -> Optional[int]:
    return r.delete(f'CONF-REC-{id_user}')


def clean_password_recovery_request(
        db: Session,
        r: Redis,
        email: Optional[str] = None,
        id_user: Optional[int] = None
) -> bool:
    if id_user is None:
        if email is None:
            raise bad_email_exception

        try:
            user = get_user_by_email(db, email)
            id_user = user.id_user
        except NotFoundException:
            raise bad_email_exception

    clean_password_recovery_cache_values(r, id_user)
    clean_password_recovery_db(db, id_user)

    return True
