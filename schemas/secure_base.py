from typing import Optional

from pydantic import BaseModel, Field


class SecureBase(BaseModel):
    data: str = Field(default=..., min_length=32)
    secure: str = Field(default=..., min_length=64)


class SecureRequest(SecureBase):
    public_pem: Optional[str] = Field(default=None, min_length=350, max_length=650)


class PublicKeyBase(BaseModel):
    pem: str = Field(..., min_length=350, max_length=650)
