from pydantic import BaseModel, Field, EmailStr

code_pattern = r"^\d{7,9}$"


class BasicResponse(BaseModel):
    operation: str
    successful: bool


class BasicPasswordChange(BaseModel):
    password: str = Field(..., min_length=8, max_length=69)


class BasicDataResponse(BaseModel):
    data: str


class BasicTicketResponse(BaseModel):
    ticket: str = Field(..., min_length=4, max_length=16)


class ChangePasswordRequest(BasicPasswordChange, BasicTicketResponse):
    email: EmailStr = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "password": "ultra-$3CR3T",
                "ticket": "AB15689rst12Gntp",
                "email": "my_email@mail.com"
            }
        }


class BasicCodeRequest(BaseModel):
    code: str = Field(..., regex=code_pattern)


class CodeRequest(BasicCodeRequest):
    email: EmailStr = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "code": "12345678",
                "email": "my_email@mail.com"
            }
        }
