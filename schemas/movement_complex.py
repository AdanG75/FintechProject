from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr

from schemas.movement_base import MovementDisplay, MovementRequest


class BaseExtraMovement(BaseModel):
    type_submov: str = Field(..., min_length=3, max_length=10)
    destination_credit: Optional[int] = Field(None, gt=0)
    id_market: Optional[str] = Field(None, min_length=12, max_length=49)
    depositor_name: Optional[str] = Field(None, min_length=2, max_length=149)
    paypal_order: Optional[str] = Field(None, min_length=8, max_length=20)


class ExtraMovement(BaseExtraMovement):
    id_detail: str = Field(..., min_length=12, max_length=49)
    movement_nature: str = Field(..., min_length=5, max_length=10)


class ExtraMovementRequest(BaseExtraMovement):
    depositor_email: Optional[EmailStr] = Field(None)


class BasicExtraMovement(MovementDisplay):
    extra: ExtraMovement = Field(...)

    class Config:
        orm_mode = True


class MovementExtraRequest(MovementRequest):
    extra: ExtraMovementRequest = Field(...)

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id_credit": 985,
                "id_performer": 452,
                "id_requester": "CLI-41fd52b6ecd6436c9dfb0e3ed95e5775",
                "type_movement": "payment",
                "amount": 99.99,
                "type_user": "market",
                "extra": {
                    "type_submov": "credit",
                    "destination_credit": None,
                    "id_market": "MKT-ad73029bc6cc436083b7ba3f9ad4a65e",
                    "depositor_name": None,
                    "paypal_order": None,
                    "depositor_email": None
                }
            }
        }


class MovementFullListDisplay(BaseModel):
    movements: List[BasicExtraMovement] = Field(..., min_items=0)

    class Config:
        orm_mode = True
