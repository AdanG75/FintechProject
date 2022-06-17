from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class AddressBase(BaseModel):
    zip_code: int = Field(..., gt=0)
    state: str = Field(..., min_length=2, max_length=79)
    city: str = Field(..., min_length=2, max_length=79)
    street: str = Field(..., min_length=2, max_length=79)
    ext_number: str = Field(..., min_length=1, max_length=19)
    inner_number: Optional[str] = Field(None, min_length=1, max_length=14)


class ClientInner(BaseModel):
    id_client: str = Field(...)
    id_user: int = Field(...)

    class Config:
        orm_mode = True


class BranchInner(BaseModel):
    id_branch: str = Field(...)
    id_market: str = Field(...)

    class Config:
        orm_mode = True


class AddressRequest(AddressBase):
    class Config:
        schema_extra = {
            "example": {
                "zip_code": 18966,
                "state": "Ciudad de México",
                "city": "CDMX",
                "street": "Avenida Principal",
                "ext_number": "5",
                "inner_number": None
            }
        }


class AddressDisplay(AddressBase):
    id_address: int = Field(...)
    clients: Optional[List[ClientInner]] = Field(None)
    branches: Optional[List[BranchInner]] = Field(None)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True



