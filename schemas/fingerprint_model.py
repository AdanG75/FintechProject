from typing import List

from pydantic import BaseModel, Field


class FingerprintSimpleModel(BaseModel):
    fingerprint: List[int]


class FingerprintB64(BaseModel):
    fingerprint: str


class FingerprintSamples(BaseModel):
    fingerprints: List[str] = Field(..., min_items=3, max_items=7)
