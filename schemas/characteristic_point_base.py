from pydantic import BaseModel, Field

from schemas.type_fingerprint import TypeChPoint


class CPBase(BaseModel):
    id_point: str = Field(..., min_length=12, max_length=40)
    pos_x: int = Field(..., ge=0, le=300)
    pos_y: int = Field(..., ge=0, le=300)
    angle: float = Field(...)
    type_point: TypeChPoint = Field(...)
