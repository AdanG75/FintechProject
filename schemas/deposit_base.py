from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from schemas.type_money import TypeMoney


class DepositBase(BaseModel):
    id_movement: int = Field(..., gt=0)
    id_destination_credit: int = Field(..., gt=0)
    type_deposit: TypeMoney = Field(...)
    depositor_name: str = Field(..., min_length=3, max_length=99)
    depositor_email: EmailStr = Field(...)


class DepositRequest(DepositBase):
    paypal_id_order: Optional[str] = Field(None, min_length=8, max_length=20)

    class Config:
        schema_extra = {
            "id_movement": 125,
            "id_destination_credit": 33,
            "depositor_name": "Juan Escutia",
            "depositor_email": "el_aventado@mail.com",
            "type_deposit": "cash",
            "paypal_id_order": None
        }


class DepositDisplay(DepositBase):
    id_deposit: str = Field(...)

    class Config:
        orm_mode = True
