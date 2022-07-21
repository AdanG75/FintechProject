from pydantic import BaseModel, Field


class BasicResponse(BaseModel):
    operation: str
    successful: bool


class BasicPasswordChange(BaseModel):
    password: str = Field(..., min_length=8, max_length=69)
