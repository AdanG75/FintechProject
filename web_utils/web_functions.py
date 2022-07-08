from datetime import datetime, timedelta
from math import floor
import random

from core.config import settings


def generate_code() -> int:
    code = floor(random.uniform(0, 9) * 10000000)

    return code


def set_expiration_time(minutes: int = settings.get_expire_minutes()) -> datetime:
    expiration_time = datetime.utcnow() + timedelta(minutes=minutes)

    return expiration_time
