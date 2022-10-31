from datetime import datetime
from typing import Optional, Union, List

from pydantic import BaseModel, Field

from schemas.type_credit import TypeCredit


money_pattern: str = r"^\$?\d{1,3}(,\d{3}){0,5}(\.\d{1,2})?$"


class CreditBase(BaseModel):
    id_client: str = Field(..., min_length=12, max_length=49)
    id_market: str = Field(..., min_length=12, max_length=49)
    id_account: Optional[int] = Field(None, gt=0)
    alias_credit: str = Field(..., min_length=3, max_length=79)
    type_credit: TypeCredit = Field(...)
    amount: Union[str, float] = Field(..., ge=0, regex=money_pattern, min_length=1, max_length=25)
    is_approved: Optional[bool] = Field(None)


class CreditRequest(CreditBase):

    class Config:
        schema_extra = {
            "example": {
                "id_client": "CLI-c65f9bf4-6cf3-46af-bfbb-ade37b1ef67b",
                "id_market": "MKT-6283921a-3939-4b4d-8a10-58a7fb43230e",
                "id_account": 128,
                "alias_credit": "Crédito de la tiendita",
                "type_credit": "local",
                "amount": 25.00
            }
        }


class CreditDisplay(CreditBase):
    id_credit: int = Field(...)
    in_process: bool = Field(...)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class ListCreditsDisplay(BaseModel):
    credits: List[CreditDisplay] = Field(...)

    class Config:
        orm_mode = True
