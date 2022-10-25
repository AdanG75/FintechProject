from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class PasswordRecoveryRequest(BaseModel):
    email: EmailStr = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "email": "myemail@mail.com"
            }
        }


class PasswordRecoveryDisplay(BaseModel):
    id_user: int = Field(...)
    code: Optional[str] = Field(None)
    expiration_time: Optional[datetime] = Field(None)
    attempts: int = Field(...)
    is_valid: bool = Field(...)

    class Config:
        orm_mode = True
