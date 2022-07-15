from fastapi import HTTPException
from sqlalchemy.exc import DBAPIError, TimeoutError, InternalError, DisconnectionError, ArgumentError, \
    CompileError, DataError, IntegrityError, InvalidRequestError, NoResultFound, MultipleResultsFound

from db.orm.exceptions_orm import db_exception, DBException, compile_exception, not_values_sent_exception, \
    wrong_data_sent_exception, not_valid_operation_exception, NotFoundException, element_not_found_exception, \
    multiple_elements_found_exception
from core.logs import write_data_log


def multiple_attempts(func):
    def wrapper(*args, **kwargs):
        global result
        success = False
        attempts = 0
        while not success:
            try:
                result = func(*args, **kwargs)
                success = True
            except HTTPException as e:
                raise e
            except NotFoundException as e:
                raise e
            except DBException:
                attempts += 1
                success = False
            finally:
                if attempts >= 10:
                    raise db_exception

        return result

    return wrapper


def full_database_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            func_result = func(*args, **kwargs)
        except HTTPException as e:
            raise e
        except NotFoundException as e:
            raise e
        except DBException as e:
            raise e
        except TimeoutError as e:
            write_data_log(e.__str__(), "ERROR")
            raise db_exception
        except InternalError as e:
            write_data_log(e.__str__(), "ERROR")
            raise db_exception
        except DisconnectionError as e:
            write_data_log(e.__str__(), "ERROR")
            raise db_exception
        except CompileError as e:
            write_data_log(e.__str__(), "ERROR")
            raise compile_exception
        except ArgumentError:
            raise wrong_data_sent_exception
        except DataError:
            raise wrong_data_sent_exception
        except IntegrityError:
            raise not_values_sent_exception
        except NoResultFound as e:
            write_data_log(e.__str__(), "WARNING")
            raise element_not_found_exception
        except MultipleResultsFound as e:
            write_data_log(e.__str__(), "WARNING")
            raise multiple_elements_found_exception
        except InvalidRequestError as e:
            write_data_log(e.__str__(), "ERROR")
            raise not_valid_operation_exception
        except DBAPIError:
            raise not_values_sent_exception

        return func_result

    return wrapper
