from pydantic import BaseModel, Field

from schemas.type_fingerprint import TypeCore


class CoreBase(BaseModel):
    id_fingerprint: str = Field(..., min_length=12, max_length=40)
    pos_x: int = Field(..., ge=0, le=300)
    pos_y: int = Field(..., ge=0, le=300)
    angle: float = Field(...)
    type_core: TypeCore = Field(...)


class CoreRequest(CoreBase):

    class Config:
        schema_extra = {
            "example": {
                "id_fingerprint": "FNP-036f5f8201aa4a1fb27af85f1b66c5aa",
                "pos_x": 45,
                "pos_y": 23,
                "angle": 156.04,
                "type_core": 'd'
            }
        }


class CoreDisplay(CoreBase):
    id_core: str = Field(...)

    class Config:
        orm_mode = True
