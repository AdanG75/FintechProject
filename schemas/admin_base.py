
from pydantic import BaseModel, Field


class AdminBase(BaseModel):
    id_user: int = Field(..., gt=0)
    full_name: str = Field(..., min_length=2, max_length=149)


class AdminRequest(AdminBase):
    class Config:
        schema_extra = {
            "example": {
                "id_user": 59,
                "full_name": "Juan Carlos Bodoque",
            }
        }


class AdminDisplay(AdminBase):
    id_admin: int = Field(...)

    class Config:
        orm_mode = True


class AdminToken(BaseModel):
    token_type: str
    access_token: str
    admin: AdminDisplay

