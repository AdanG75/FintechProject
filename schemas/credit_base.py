from datetime import datetime

from pydantic import BaseModel, Field

from schemas.type_credit import TypeCredit


class CreditBase(BaseModel):
    id_client: str = Field(..., min_length=12, max_length=49)
    id_market: str = Field(..., min_length=12, max_length=49)
    id_account: int = Field(..., gt=0)
    alias_credit: str = Field(..., min_length=3, max_length=79)
    type_credit: TypeCredit = Field(...)
    amount: float = Field(..., ge=0)


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
    id_credit: int = Field(...),
    is_approved: bool = Field(...),
    in_process: bool = Field(...),
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True