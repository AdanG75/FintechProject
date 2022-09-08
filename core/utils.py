import base64
import binascii
import datetime
import json
import random
import string
from typing import List, Union, Optional

from email_validator import validate_email, EmailNotValidError
from phonenumbers import parse, is_valid_number
from pydantic import BaseModel

from db.orm.exceptions_orm import bad_email_exception


def bytes_to_int_array(data: bytes) -> List[int]:
    int_array = list()

    for byte in data:
        int_array.append(byte)

    return int_array


def int_array_to_bytes(array: List[int]) -> bytes:
    """
    Convert an iterable object to bytes.
    Each value of the iterable object must be grater or equal than 0 and lower than 256.

    :param array: (List[int]) - The dato to convert to bytes.

    :return: (bytes) - The data in bytes format
    """
    data_in_bytes = bytes(bytearray(array))

    return data_in_bytes


def save_json_file(data: dict, file_name: str, path: str = "./") -> bool:
    if not file_name.endswith(".json"):
        file_name = file_name + ".json"

    if path.isspace() or path == "":
        path = "./"

    try:
        with open(path + file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.close()
    except Exception:
        raise FileExistsError

    return True


def save_object_as_json(
        object_model: BaseModel,
        path_json: str = "./",
        name_json: str = "object.json"
) -> bool:
    result = save_json_file(data=object_model.dict(), file_name=name_json, path=path_json)

    return result


def read_json_file(path: str, mode: str = "global"):
    if not path.endswith('.json'):
        path += '.json'

    func_mode = mode.lower()

    def open_file(func):
        def wrapper(*args, **kwargs):
            with open(
                    file=path,
                    mode='r',
                    encoding='utf-8'
            ) as file:
                my_json = json.load(file)

                if func_mode == "local":
                    result = func(my_json)
                else:
                    result = func(my_json, *args, **kwargs)

                file.close()

            return result

        return wrapper

    return open_file


def get_current_utc_timestamp() -> float:
    now = datetime.datetime.utcnow()

    return now.timestamp()


def get_timestamp_from_string(datetime_formatted: str) -> float:
    format_datetime = "%Y-%m-%d  %H:%M:%S"
    datetime_str = datetime.datetime.strptime(datetime_formatted, format_datetime)
    ts = datetime_str.timestamp()

    return ts


def cast_bytes_to_base64(value: bytes) -> str:
    """
    Convert bytes to string using base64 encoding and utf-8 to represent as string.
    :param value: (bytes) - Value to cast to string (str).
    :return: (str) - A string which represent the value.
    """
    return binascii.b2a_base64(value).decode("utf-8").strip()


def cast_base64_to_bytes(value: str) -> bytes:
    """
    Convert base64 encoding string with utf-8 to bytes.
    :param value: (str) - Value to cast to bytes.
    :return: (bytes) - Bytes which represent the value.
    """
    value_bytes = value.encode('utf-8')
    return base64.b64decode(value_bytes)


def get_bytes(value: Union[str, bytes]) -> bytes:
    """
    Use when you receive encrypt data as: cipher message, a key, a password, an initialization vector, etc.
    Convert base64 encoding string with utf-8 to bytes if value is of type string.
    In other case return the same value.
    :param value: (Union[str, bytes]) - Value to convert in bytes if it is necessary.
    :return: (bytes) - Bytes which represent the value.
    """
    if isinstance(value, str):
        return_bytes = cast_base64_to_bytes(value=value)
    else:
        return_bytes = value

    return return_bytes


def set_phone_number_format(phone: str) -> str:
    phone_without_spaces_and_dashes = phone.replace(" ", "").replace("-", "")

    if not phone_without_spaces_and_dashes.startswith('+'):
        final_phone = '+' + phone_without_spaces_and_dashes
    else:
        final_phone = phone_without_spaces_and_dashes

    return final_phone


def is_valid_phone_number(phone: str, region: Optional[str] = None) -> bool:
    number_object = parse(phone, region)
    is_valid = is_valid_number(number_object)

    return is_valid


def check_email(email: str, check: bool = True, mode: str = 'normal') -> bool:
    if check:
        try:
            validate_email(email)
        except EmailNotValidError:
            if mode == 'exception':
                raise bad_email_exception
            else:
                return False

    return True


def money_str_to_float(money: str) -> float:
    money_float = float(money.replace("$", "").replace(",", ""))

    return money_float


def replace_spaces_with_hyphens(my_string: str) -> str:
    return my_string.strip().replace(' ', '-').lower()


def generate_random_string(length: int) -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))
