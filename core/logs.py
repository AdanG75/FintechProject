
from enum import Enum
from typing import Union

from fastapi import HTTPException
from google.cloud import logging

from starlette import status

from core.config import settings


def get_logging_client():
    logging_client = logging.Client()

    try:
        yield logging_client
    finally:
        logging_client.close()


def write_data_log(data: str, severity: str = "INFO", logger_name: str = 'fintech75') -> bool:
    """
    Write a log entry
    :param data: (str) - Text to show into the log
    :param severity: (str) - Can be whatever value into Enum class LogSeverity
    :param logger_name: (str) - The name of log

    :return: True is all were OK

    :raise: HTTPException with code 503 if system couldn't write the log
    """
    logging_client = logging.Client()
    logger = logging_client.logger(logger_name)

    try:
        LogSeverity(severity).value
    except ValueError:
        severity = LogSeverity.INFO.value

    # Writes the log entry
    try:
        logger.log_text(data, severity=severity)
    except Exception:
        logging_client.close()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible create log, please try again."
        )

    logging_client.close()
    return True


def show_error_message(error: Union[Exception, str]) -> None:
    """
    Show an error in console or log

    :param error: (Exception, str) The error to report

    :return: (None)
    """
    msg = error.__str__() if isinstance(error, Exception) else error

    if settings.is_on_cloud():
        write_data_log(msg, "ERROR")
    else:
        print(msg)


class LogSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"
    EMERGENCY = "EMERGENCY"
