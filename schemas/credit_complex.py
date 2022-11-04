from typing import List

from pydantic import BaseModel, Field

from schemas.credit_base import CreditDisplay
from schemas.movement_complex import BasicExtraMovement


class OwnerInner(BaseModel):
    name_owner: str = Field(..., min_length=2, max_length=150)
    type_owner: str = Field(..., min_length=5, max_length=9)


class CreditComplexProfile(BaseModel):
    credit: CreditDisplay = Field(...)
    movements: List[BasicExtraMovement] = Field(..., min_items=0)
    owner: OwnerInner = Field(...)
