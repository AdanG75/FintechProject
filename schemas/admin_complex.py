from pydantic import BaseModel, Field

from schemas.admin_base import AdminRequest, AdminDisplay
from schemas.user_base import UserRequest, UserBasicDisplay


class AdminFullRequest(BaseModel):
    user: UserRequest = Field(...)
    admin: AdminRequest = Field(...)


class AdminFullDisplay(BaseModel):
    user: UserBasicDisplay = Field(...)
    admin: AdminDisplay = Field(...)

    class Config:
        orm_mode = True
