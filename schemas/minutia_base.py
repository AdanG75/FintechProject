from pydantic import BaseModel, Field

from schemas.type_fingerprint import TypeMinutia


class MinutiaBase(BaseModel):
    id_fingerprint: str = Field(..., min_length=12, max_length=40)
    pos_x: int = Field(..., ge=0, le=300)
    pos_y: int = Field(..., ge=0, le=300)
    angle: float = Field(...)
    type_minutia: TypeMinutia = Field(...)


class MinutiaRequest(MinutiaBase):

    class Config:
        schema_extra = {
            "example": {
                "id_fingerprint": "FNP-036f5f8201aa4a1fb27af85f1b66c5aa",
                "pos_x": 136,
                "pos_y": 223,
                "angle": 84.00,
                "type_minutia": 'e'
            }
        }


class MinutiaDisplay(MinutiaBase):
    id_minutia: str = Field(...)

    class Config:
        orm_mode = True
