from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class LoginAttemptBase(BaseModel):
    email: EmailStr = Field(...)


class LoginAttemptRequest(LoginAttemptBase):
    id_user: int = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "id_user": 18,
                "email": "anemail@mail.com"
            }
        }


class LoginAttemptDisplay(LoginAttemptBase):
    attempts: int = Field(...)
    next_attempt_time: Optional[datetime] = Field(None)

    class Config:
        orm_mode = True
