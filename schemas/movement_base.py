from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, EmailStr

from schemas.type_money import TypeMoney
from schemas.type_movement import TypeMovement
from schemas.type_transfer import TypeTransfer
from schemas.type_user import TypeUser


money_pattern: str = r"^\$?\d{1,3}(,\d{3}){0,5}(\.\d{1,2})?$"


class MovementBase(BaseModel):
    id_credit: Optional[int] = Field(None, gt=0)
    id_performer: int = Field(..., gt=0)
    id_requester: Optional[str] = Field(None, min_length=12, max_length=49)
    type_movement: TypeMovement = Field(...)
    amount: Union[str, float] = Field(..., gt=0, regex=money_pattern, min_length=1, max_length=25)


class MovementRequest(MovementBase):
    type_user: TypeUser = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "id_credit": 985,
                "id_performer": 452,
                "id_requester": "CLI-41fd52b6ecd6436c9dfb0e3ed95e5775",
                "type_movement": "payment",
                "amount": 99.99,
                "type_user": "market"
            }
        }


class MovementDisplay(MovementBase):
    id_movement: int = Field(...)
    authorized: bool = Field(...)
    in_process: bool = Field(...)
    successful: Optional[bool] = Field(None)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class MovementTypeBase(BaseModel):
    id_credit: Optional[int] = Field(..., gt=0)
    type_movement: TypeMovement = Field(...)
    amount: Union[str, float] = Field(..., gt=0, regex=money_pattern, min_length=1, max_length=25)
    type_submov: TypeMoney = Field(...)


class MovementTypeRequest(MovementTypeBase):
    destination_credit: Optional[int] = Field(None, gt=0)
    id_market: Optional[str] = Field(None, min_length=12, max_length=49)
    depositor_name: Optional[str] = Field(None, min_length=2, max_length=149)
    depositor_email: Optional[EmailStr] = Field(None)
    type_transfer: Optional[TypeTransfer] = Field(None)

    class Config:
        schema_extra = {
            "example": {
                "id_credit": 985,
                "type_movement": "payment",
                "amount": 99.99,
                "type_submov": "paypal",
                "destination_credit": None,
                "id_market": "MKT-ad73029bc6cc436083b7ba3f9ad4a65e",
                "depositor_name": None,
                "depositor_email": None,
                "type_transfer": None
            }
        }


class UserDataMovement(BaseModel):
    id_performer: int = Field(..., gt=0)
    type_user: TypeUser = Field(...)
    id_type_performer: str = Field(..., min_length=12, max_length=49)
    id_requester: Optional[str] = Field(None, min_length=12, max_length=49)
