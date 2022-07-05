from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from schemas.type_user import TypeUser


class AccountBase(BaseModel):
    alias_account: str = Field(..., min_length=4, max_length=79)
    paypal_email: Optional[EmailStr] = Field(None)
    type_owner: TypeUser = Field(...)
    main_account: bool = Field(True)


class UserInner(BaseModel):
    id_user: int = Field(...)
    email: EmailStr = Field(...)

    class Config:
        orm_mode = True


class AccountRequest(AccountBase):
    id_user: int = Field(..., gt=0)
    paypal_id_client: str = Field(..., min_length=12, max_length=72)
    paypal_secret: str = Field(..., min_length=12, max_length=72)

    class Config:
        schema_extra = {
            "example": {
                "id_user": 1,
                "alias_account": "cuenta maestra",
                "paypal_email": "client@mail.com",
                "paypal_id_client": "XXXXXXXXXXXXXXX",
                "paypal_secret": "*****************",
                "type_owner": "client",
                "main_account": True
            }
        }


class AccountDisplay(AccountBase):
    id_account: int = Field(...)
    created_time: datetime = Field(...)
    user: UserInner = Field(...)

    class Config:
        orm_mode = True



