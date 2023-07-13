from typing import List

from pydantic import BaseModel, Field


b64_pattern = r'^[A-Za-z0-9+/\r\n]+={0,2}$'


class FingerprintSimpleModel(BaseModel):
    fingerprint: List[int]


class FingerprintB64(BaseModel):
    fingerprint: str = Field(..., regex=b64_pattern, min_length=150)


class FingerprintSamples(BaseModel):
    fingerprints: List[str] = Field(..., min_items=3, max_items=7)
