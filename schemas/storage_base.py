from pydantic import BaseModel


class StorageBase(BaseModel):
    name: str
    id: str
    location: str
    created_at: str
    storage_class: str
