from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from schemas.type_movement import TypeMovement
from schemas.type_user import TypeUser


class MovementBase(BaseModel):
    id_credit: int = Field(..., gt=0)
    id_performer: int = Field(..., gt=0)
    id_requester: Optional[str] = Field(None, min_length=12, max_length=49)
    type_movement: TypeMovement = Field(...)
    amount: float = Field(..., gt=0)


class MovementRequest(MovementBase):
    type_user: TypeUser = Field(...)

    class Config:
        schema_extra = {
            "id_credit": 985,
            "id_performer": 452,
            "id_requester": "CLI-41fd52b6-ecd6-436c-9dfb-0e3ed95e5775",
            "type_movement": "payment",
            "amount": 99.99,
            "type_user": "market"
        }


class MovementDisplay(MovementBase):
    id_movement: int = Field(...)
    in_process: bool = Field(...)
    successful: bool = Field(...)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True
