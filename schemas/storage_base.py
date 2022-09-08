from datetime import datetime

from pydantic import BaseModel, Field


class StorageBase(BaseModel):
    name: str = Field(..., min_length=4, max_length=79)
    id: str = Field(..., min_length=3, max_length=79)
    location: str = Field(..., min_length=2, max_length=31)
    created_at: datetime = Field(...)
    storage_class: str = Field(..., min_length=2, max_length=15)


class StorageSimple(BaseModel):
    bucket_name: str = Field(..., min_length=4, max_length=79)


class StorageSimpleFile(StorageSimple):
    file_saved: str = Field(..., min_length=4, max_length=79)
