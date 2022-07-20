from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


time_pattern: str = r"^\d{4}[-/.]{1}\d\d[-/.]{1}\d\d[ T]{1}\d\d:\d\d:\d\d ?$"


class SessionBase(BaseModel):
    id_user: int = Field(..., gt=0)


class SessionStrRequest(SessionBase):
    session_start: Optional[str] = Field(None, regex=time_pattern, min_length=15, max_length=21)
    session_finish: Optional[str] = Field(None, regex=time_pattern, min_length=15, max_length=21)

    class Config:
        schema_extra = {
            "example": {
                "id_user": 78,
                "session_start": "2022-08-17 21:01:36",
                "session_finish": "2022-08-18 00:52:42"
            }
        }


class SessionRequest(SessionBase):
    session_start: Optional[datetime] = Field(None)
    session_finish: Optional[datetime] = Field(None)

    class Config:
        schema_extra = {
            "example": {
                "id_user": 78,
                "session_start": "2022-08-17 21:01:36",
                "session_finish": "2022-08-18 00:52:42"
            }
        }


class SessionDisplay(SessionBase):
    id_session: int = Field(...)
    session_start: datetime = Field(...)
    session_finish: Optional[datetime] = Field(None)

    class Config:
        orm_mode = True
