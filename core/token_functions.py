
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt

from core.config import settings

SECRET_KEY: str = settings.get_secret_key()
ALGORITHM: str = settings.get_algorithm()
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.get_expire_minutes()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
