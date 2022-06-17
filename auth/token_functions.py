
from typing import Optional
from datetime import datetime, timedelta

from fastapi import HTTPException
from jose import jwt
from starlette import status

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

    to_encode.update({"exp": expire.timestamp()})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def is_token_expired(exp_time: int) -> bool:
    curr_dt = datetime.utcnow()
    timestamp = curr_dt.timestamp()

    if timestamp > exp_time:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )

    return False
