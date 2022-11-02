from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, HttpUrl


class MarketBase(BaseModel):
    id_user: int = Field(..., gt=0)
    type_market: str = Field(..., min_length=3, max_length=149)
    web_page: Optional[HttpUrl] = Field(None)
    rfc: Optional[str] = Field(None, min_length=10, max_length=20)


class MarketRequest(MarketBase):
    class Config:
        schema_extra = {
            "example": {
                "id_user": 78,
                "type_market": "Taqueria",
                "web_page": "https://www.facebook.com/1478526",
                "rfc": None
            }
        }


class BranchInner(BaseModel):
    id_branch: str = Field(...)
    branch_name: str = Field(...)
    service_hours: str = Field(...)
    phone: Optional[str] = Field(None)
    created_time: datetime = Field(...)

    class Config:
        orm_mode = True


class MarketDisplay(MarketBase):
    id_market: str = Field(...)

    branches: List[BranchInner] = Field(...)

    class Config:
        orm_mode = True


class MarketBasicDisplay(MarketBase):
    id_market: str = Field(...)

    class Config:
        orm_mode = True
