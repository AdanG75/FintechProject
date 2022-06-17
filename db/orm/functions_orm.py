from db.orm.exceptions_orm import db_exception


def multiple_attempts(func):
    def wrapper(*args, **kwargs):
        global result
        success = False
        attempts = 0
        while not success:
            try:
                result = func(*args, **kwargs)
                success = True
            except db_exception:
                attempts += 1
                success = False
            finally:
                if attempts >= 10:
                    raise db_exception

        return result

    return wrapper
