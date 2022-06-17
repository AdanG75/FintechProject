from typing import List

from pydantic import BaseModel


class FingerprintSimpleModel(BaseModel):
    fingerprint: List[int]


class FingerprintB64(BaseModel):
    fingerprint: str
