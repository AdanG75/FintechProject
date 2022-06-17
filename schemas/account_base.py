from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from schemas.type_user import TypeUser


class AccountBase(BaseModel):
    paypal_email: Optional[EmailStr] = Field(None)
    type_owner: TypeUser = Field(...)
    main_account: bool = Field(True)
    system_account: bool = Field(False)


class UserInner(BaseModel):
    id_user: int = Field(...)
    email: EmailStr = Field(...)

    class Config:
        orm_mode = True


class AccountRequest(AccountBase):
    id_user: int = Field(..., gt=0)

    class Config:
        schema_extra = {
            "example": {
                "id_user": 1,
                "paypal_email": "client@mail.com",
                "type_owner": "client",
                "main_account": True,
                "system_account": False
            }
        }


class AccountDisplay(AccountBase):
    id_account: int = Field(...)
    user: UserInner = Field(...)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True



