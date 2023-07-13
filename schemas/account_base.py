from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from schemas.type_user import TypeUser

email_pattern = r"[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.?){2,4}$"


class AccountBase(BaseModel):
    alias_account: str = Field(..., min_length=4, max_length=79)
    paypal_email: Optional[str] = Field(None, regex=email_pattern, min_length=5, max_length=79)
    type_owner: TypeUser = Field(...)
    main_account: bool = Field(True)


class UserInner(BaseModel):
    id_user: int = Field(...)
    email: EmailStr = Field(...)

    class Config:
        orm_mode = True


class AccountRequest(AccountBase):
    id_user: int = Field(..., gt=0)
    paypal_id_client: Optional[str] = Field(None, min_length=20, max_length=85)
    paypal_secret: Optional[str] = Field(None, min_length=20, max_length=85)

    class Config:
        schema_extra = {
            "example": {
                "id_user": 1,
                "alias_account": "cuenta maestra",
                "paypal_email": "client@mail.com",
                "paypal_id_client": "XXXXXXXXXXXXXXXXXXXXXX",
                "paypal_secret": "************************",
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
