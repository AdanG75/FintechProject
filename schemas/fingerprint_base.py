from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from schemas.type_fingerprint import FingerprintType
from schemas.type_quality import QualityType
from schemas.type_request import RequestType


alias_pattern: str = r"^[A-Za-z0-9_ -]+$"


class FingerprintBase(BaseModel):
    id_client: str = Field(..., min_length=12, max_length=49)
    alias_fingerprint: str = Field(..., regex=alias_pattern, min_length=2, max_length=79)
    main_fingerprint: bool = Field(...)


class FingerprintRequest(FingerprintBase):
    url_fingerprint: str = Field(..., min_length=8, max_length=149)
    fingerprint_type: FingerprintType = Field(...)
    quality: QualityType = Field(...)
    spectral_index: float = Field(..., gt=0, lt=1.1)
    spatial_index: float = Field(..., gt=0, lt=1.1)

    class Config:
        schema_extra = {
            "example": {
                "id_client": "CLI-e549787795a645ab9caf3f9e785c8884",
                "alias_fingerprint": "Indice derecho",
                "main_fingerprint": True,
                "url_fingerprint": "BKT-e549787795a645ab9caf3f9e785c8884/indice-derecho1456",
                "fingerprint_type": "match",
                "quality": "good",
                "spectral_index": 0.75326598,
                "spatial_index": 0.56421398
            }
        }


class FingerprintUpdateRequest(BaseModel):
    alias_fingerprint: str = Field(..., regex=alias_pattern, min_length=2, max_length=79)
    main_fingerprint: bool = Field(...)
    request: RequestType = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "id_client": "CLI-e549787795a645ab9caf3f9e785c8884",
                "alias_fingerprint": "Indice izquierdo",
                "main_fingerprint": True,
                "request": "update"
            }
        }


class FingerprintAddRequest(FingerprintBase):
    fingerprint_data: str = Field(..., min_length=64)
    main_fingerprint: bool = Field(...)
    alias_fingerprint: str = Field(..., regex=alias_pattern, min_length=2, max_length=79)


class ClientInner(BaseModel):
    id_client: str = Field(...)
    id_user: int = Field(...)

    class Config:
        orm_mode = True


class CorePointInner(BaseModel):
    id_characteristic: str = Field(...)
    pos_x: int = Field(...)
    pos_y: int = Field(...)
    angle: int = Field(...)
    type: str = Field(...)

    class Config:
        orm_mode = True


class MinutiaInner(BaseModel):
    id_index: str = Field(...)
    pos_x: int = Field(...)
    pos_y: int = Field(...)
    angle: int = Field(...)
    type: str = Field(...)

    class Config:
        orm_mode = True


class FingerprintBasicDisplay(FingerprintBase):
    id_fingerprint: str = Field(...)
    created_time: datetime = Field(...)

    client: Optional[ClientInner] = Field(None)

    class Config:
        orm_mode = True


class FingerprintDisplay(FingerprintBasicDisplay):
    url_fingerprint: str = Field(..., min_length=8, max_length=149)

    core_points: Optional[List[CorePointInner]] = Field(None)
    minutiae: Optional[List[MinutiaInner]] = Field(None)

    class Config:
        orm_mode = True
