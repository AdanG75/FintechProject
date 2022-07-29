from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from schemas.type_user import TypeUser


class AddressBase(BaseModel):
    is_main: bool = Field(...)
    zip_code: int = Field(..., gt=0)
    state: str = Field(..., min_length=2, max_length=79)
    city: Optional[str] = Field(None, min_length=2, max_length=79)
    neighborhood: Optional[str] = Field(None, min_length=3, max_length=79)
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
    id_branch: Optional[str] = Field(None, min_length=8, max_length=49)
    id_client: Optional[str] = Field(None, min_length=8, max_length=49)
    type_owner: TypeUser = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "id_branch": "BR-asdf-ewefvrf-dwvref",
                "id_client": None,
                "type_owner": "market",
                "is_main": True,
                "zip_code": 18966,
                "state": "Ciudad de México",
                "city": "CDMX",
                "neighborhood": "La gran Loma",
                "street": "Avenida Principal",
                "ext_number": "5",
                "inner_number": None
            }
        }


class AddressDisplay(AddressBase):
    id_address: int = Field(...)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class AddressDisplayClient(AddressDisplay):
    client: Optional[ClientInner] = Field(None)

    class Config:
        orm_mode = True


class AddressDisplayMarket(AddressDisplay):
    branch: Optional[BranchInner] = Field(None)

    class Config:
        orm_mode = True
