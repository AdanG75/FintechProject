from typing import Optional

from pydantic import BaseModel, Field

from schemas.type_money import TypeMoney


class PaymentBase(BaseModel):
    id_movement: int = Field(..., gt=0)
    id_market: str = Field(..., min_length=12, max_length=49)
    type_payment: TypeMoney = Field(...)


class PaymentRequest(PaymentBase):
    paypal_id_order: Optional[str] = Field(None, min_length=8, max_length=20)

    class Config:
        schema_extra = {
            "example": {
                "id_movement": 99,
                "id_market": "MKT-191a9ec9-8c3b-4c16-be06-3a0f34989a6b",
                "type_payment": "local",
                "paypal_id_order": None
            }
        }


class PaymentDisplay(PaymentBase):
    id_payment: str = Field(...)

    class Config:
        orm_mode = True
