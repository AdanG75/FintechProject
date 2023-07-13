from typing import List

from pydantic import BaseModel, Field

from schemas.credit_base import CreditDisplay, CreditBase
from schemas.movement_complex import BasicExtraMovement


class OwnerInner(BaseModel):
    name_owner: str = Field(..., min_length=2, max_length=150)
    type_owner: str = Field(..., min_length=5, max_length=9)


class OwnersInner(BaseModel):
    market_name: str = Field(..., min_length=2, max_length=79)
    client_name: str = Field(..., min_length=2, max_length=160)


class CreditComplexProfile(BaseModel):
    credit: CreditDisplay = Field(...)
    movements: List[BasicExtraMovement] = Field(..., min_items=0)
    owner: OwnerInner = Field(...)


class CreditComplexSummary(BaseModel):
    credit: CreditBase = Field(...)
    owners: OwnersInner = Field(...)
    id_pre_credit: str = Field(..., min_length=16, max_length=48)
