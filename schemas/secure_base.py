from pydantic import BaseModel, Field


class SecureBase(BaseModel):
    data: str = Field(default=..., min_length=32)
    secure: str = Field(default=..., min_length=64)
