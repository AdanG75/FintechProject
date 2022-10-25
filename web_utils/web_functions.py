from datetime import datetime, timedelta
from math import floor
import random

from core.config import settings


def generate_code() -> int:
    code = floor(random.uniform(0, 9) * 10000000)

    return code


def generate_code_str() -> str:
    int_code = generate_code()
    str_code = str(int_code)

    # Code's length should be 8 so if it is less, we add zeros at begin
    new_zeros = 8 - len(str_code)
    if new_zeros > 0:
        zeros_char = ['0' for _ in range(0, new_zeros)]
        zeros_str = ''.join(zeros_char)
        str_code = zeros_str + str_code

    return str_code


def set_expiration_time(minutes: int = settings.get_expire_minutes()) -> datetime:
    expiration_time = datetime.utcnow() + timedelta(minutes=minutes)

    return expiration_time
