from fastapi import HTTPException

from db.orm.exceptions_orm import db_exception, DBException


def multiple_attempts(func):
    def wrapper(*args, **kwargs):
        global result
        success = False
        attempts = 0
        while not success:
            try:
                result = func(*args, **kwargs)
                success = True
            except DBException:
                attempts += 1
                success = False
            except HTTPException as e:
                raise e
            finally:
                if attempts >= 10:
                    raise db_exception

        return result

    return wrapper
