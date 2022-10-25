from redis.client import Redis
from sqlalchemy.orm import Session

from core.cache import batch_save
from core.logs import show_error_message
from db.orm.exceptions_orm import NotFoundException, bad_email_exception, error_while_generating_code_exception
from db.orm.password_recoveries_orm import create_code_to_recover_password
from db.orm.users_orm import get_user_by_email


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

    result = create_values_in_cache_to_recover(r, code_object.id_recover, code_object.code)

    if not result:
        raise error_while_generating_code_exception

    return code_object.code


def create_values_in_cache_to_recover(
        r: Redis,
        recover_id: int,
        code: str
) -> bool:

    password_recovery_values = {
        f'CODE-REC-{recover_id}': code,
        f'ATMS-REC-{recover_id}': 0
    }

    results = batch_save(r, password_recovery_values, seconds=3600)

    if results.count(False) > 0:
        return False

    return True
