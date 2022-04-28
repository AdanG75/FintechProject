
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from decouple import config

SECRET_KEY: str = config('SECRET_KEY')
ALGORITHM: str = config('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(config('ACCESS_TOKEN_EXPIRE_MINUTES'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
