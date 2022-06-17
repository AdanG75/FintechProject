from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

pattern_service_hours: str = "^\d\d?:\d{2}(\s?[aApP]\.?[mM]\.?\s?)?[\s-]{1,3}\d\d?:\d{2}(\s?[aApP]\.?[mM]\.?\s?)?$"


class BranchBase(BaseModel):
    branch_name: str = Field(..., min_length=1, max_length=79)
    service_hours: str = Field(..., regex=pattern_service_hours, min_length=9, max_length=24)
    phone: Optional[str] = Field(None, min_length=7, max_length=25)
    password: str = Field(..., min_length=8, max_length=49)


class MarketInner(BaseModel):
    id_market: str = Field(...)
    id_user: int = Field(...)
    type_market: str = Field(...)
    web_page: Optional[HttpUrl] = Field(None)
    rfc: Optional[str] = Field(None)

    class Config:
        orm_mode = True


class AddressInner(BaseModel):
    id_address: int = Field(...)
    zip_code: int = Field(...)
    state: str = Field(...)
    city: str = Field(...)
    street: str = Field(...)
    ext_number: str = Field(...)
    inner_number: Optional[str] = Field(None)

    class Config:
        orm_mode = True


class BranchRequest(BranchBase):
    class Config:
        schema_extra = {
            "example": {
                "branch_name": "Sucursal 2",
                "service_hours": "09:00 - 21:00",
                "password": "8745213sf"
            }
        }


class BranchUpdateRequest(BranchBase):
    id_market: str = Field(..., min_length=12, max_length=49)
    id_address: int = Field(..., gt=0)

    class Config:
        schema_extra = {
            "example": {
                "id_market": "MKT-78521rgrgecx",
                "id_address": 45,
                "branch_name": "Sucursal 2",
                "service_hours": "09:00 - 21:00",
                "password": "8745213sf"
            }
        }


class BranchDisplay(BranchBase):
    id_branch: str = Field(...)
    id_market: str = Field(...)
    id_address: int = Field(...)
    created_time: datetime = Field(...)

    market: MarketInner = Field(...)
    address: AddressInner = Field(...)

    class Config:
        orm_mode = True

