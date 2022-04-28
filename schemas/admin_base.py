
from pydantic import BaseModel, EmailStr, Field


class AdminBase(BaseModel):
    username: str = Field(min_length=4, max_length=49)
    email: EmailStr = Field(...)


class AdminRequest(AdminBase):
    password: str = Field(min_length=8, max_length=31)

    class Config:
        schema_extra = {
            "example": {
                "username": "super_user",
                "email": "mail@fintech75.com",
                "password": "secret-password"
            }
        }


class AdminDisplay(AdminBase):
    id: int = Field(gt=0)

    class Config:
        orm_mode = True


class AdminToken(BaseModel):
    token_type: str
    access_token: str
    admin: AdminDisplay
