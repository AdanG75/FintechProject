from pydantic import BaseModel, Field


class BasicResponse(BaseModel):
    operation: str
    successful: bool


class BasicPasswordChange(BaseModel):
    password: str = Field(..., min_length=8, max_length=69)


class BasicDataResponse(BaseModel):
    data: str


class BasicTicketResponse(BaseModel):
    ticket: str = Field(..., min_length=4, max_length=16)
