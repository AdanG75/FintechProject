from pydantic import BaseModel


class BasicResponse(BaseModel):
    operation: str
    successful: bool
