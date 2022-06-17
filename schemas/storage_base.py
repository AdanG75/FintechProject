from pydantic import BaseModel, Field


class StorageBase(BaseModel):
    name: str = Field(..., min_length=4, max_length=79)
    id: str = Field(..., min_length=3, max_length=79)
    location: str = Field(..., max_length=2, min_length=31)
    created_at: str = Field(...)
    storage_class: str = Field(..., min_length=2, max_length=15)
