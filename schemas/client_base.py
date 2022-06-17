from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    id_user: int = Field(..., gt=0)
    id_address: int = Field(..., gt=0)
    last_name: str = Field(..., min_length=2, max_length=99)
    birth_date: date = Field(...)
    phone: Optional[str] = Field(None, min_length=7, max_length=25)


class AddressInner(BaseModel):
    zip_code: int = Field(...)
    state: str = Field(...)
    city: str = Field(...)
    street: str = Field(...)
    ext_number: str = Field(...)
    inner_number: Optional[str] = Field(None)

    class Config:
        orm_mode = True


class FingerprintInner(BaseModel):
    id_fingerprint: str = Field(...)
    url_fingerprint: str = Field(..., min_length=8, max_length=149)
    main_fingerprint: bool = Field(...)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class ClientRequest(ClientBase):
    id_client: str = Field(...)


class ClientDisplay(ClientBase):
    id_client: str = Field(...)

    address: AddressInner = Field(...)
    fingerprints: Optional[List[FingerprintInner]] = Field(None)

    class Config:
        orm_mode = True





