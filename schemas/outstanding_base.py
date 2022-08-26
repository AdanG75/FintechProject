from datetime import datetime
from typing import Union, Optional

from pydantic import BaseModel, Field


money_pattern: str = r"^\$?\d{1,3}(,\d{3}){0,5}(\.\d{1,2})?$"


class OutstandingPaymentBase(BaseModel):
    id_market: str = Field(..., min_length=12, max_length=49)
    amount: Union[str, float] = Field(..., ge=0, regex=money_pattern, min_length=1, max_length=25)


class OutstandingPaymentRequest(OutstandingPaymentBase):

    class Config:
        schema_extra = {
            "id_market": "MKT-d7542603bf4c49e79c3d11170d5eaf12",
            "amount": 99.99
        }


class OutstandingPaymentDisplay(OutstandingPaymentBase):
    id_outstanding: int = Field(...)
    past_amount: Union[str, float] = Field(..., ge=0, regex=money_pattern, min_length=1, max_length=25)
    in_process: bool = Field(...)
    last_cash_closing: Optional[datetime] = Field(None)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True
