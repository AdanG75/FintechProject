from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    id_user: int = Field(..., gt=0)
    last_name: str = Field(..., min_length=2, max_length=99)
    birth_date: date = Field(...)


class AddressInner(BaseModel):
    id_address: int = Field(...)
    zip_code: int = Field(...)
    state: str = Field(...)
    city: str = Field(...)
    neighborhood: str = Field(...)
    street: str = Field(...)
    ext_number: str = Field(...)
    inner_number: Optional[str] = Field(None)

    class Config:
        orm_mode = True


class FingerprintInner(BaseModel):
    id_fingerprint: str = Field(...)
    alias_fingerprint: str = Field(...)
    url_fingerprint: str = Field(..., min_length=8, max_length=149)
    main_fingerprint: bool = Field(...)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class ClientRequest(ClientBase):

    class Config:
        schema_extra = {
            "example": {
                "id_user": 45,
                "last_name": "Aquino",
                "birth_date": "1974/09/16"
            }
        }


class ClientDisplay(ClientBase):
    id_client: str = Field(...)
    age: int = Field(...)

    addresses: List[AddressInner] = Field(...)
    fingerprints: Optional[List[FingerprintInner]] = Field(None)

    class Config:
        orm_mode = True





