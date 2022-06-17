from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    message: str = Field(default=..., min_length=4, max_length=2048)
    user: str = Field(default=..., min_length=4, max_length=24)


class MessageRequest(MessageBase):
    datetime: str = Field(default=..., min_length=8, max_length=32)


class MessageDisplay(MessageBase):
    datetime: float = Field(default=..., gt=0)
