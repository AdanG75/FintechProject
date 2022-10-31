from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field("bearer", min_length=3, max_length=15)
    user_id: int = Field(..., gt=0)
    type_user: str = Field(..., min_length=5, max_length=8)

    class Config:
        orm_mode = True


class TokenSummary(BaseModel):
    id_user: int = Field(..., gt=0)
    type_user: str = Field(..., min_length=4, max_length=8)
    id_type: str = Field(..., min_length=20, max_length=40)
    id_session: int = Field(..., gt=0)
