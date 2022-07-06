from typing import Optional

from pydantic import BaseModel, Field

from schemas.type_money import TypeMoney


class TransferBase(BaseModel):
    id_movement: int = Field(...)
    id_destination_credit: int = Field(...)
    type_transfer: TypeMoney = Field(...)


class TransferRequest(TransferBase):
    paypal_id_order: Optional[str] = Field(None, min_length=8, max_length=20)

    class Config:
        schema_extra = {
            "id_movement": 512,
            "id_destination_credit": 84,
            "type_transfer": "paypal",
            "paypal_id_order": "9B265168CF0213620"
        }


class TransferDisplay(TransferBase):
    id_transfer: str = Field(...)

    class Config:
        orm_mode: True
