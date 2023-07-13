from pydantic import BaseModel, Field

from schemas.type_money import TypeMoney


class WithdrawBase(BaseModel):
    id_movement: int = Field(..., gt=0)
    type_withdraw: TypeMoney = Field(...)


class WithdrawRequest(WithdrawBase):

    class Config:
        schema_extra = {
            "example": {
                "id_movement": 274,
                "type_withdraw": "cash"
            }
        }


class WithdrawDisplay(WithdrawBase):
    id_withdraw: str = Field(...)

    class Config:
        orm_mode = True
