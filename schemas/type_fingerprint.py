from enum import Enum


class FingerprintType(Enum):
    authentication: str = "authentication"
    test: str = "test"
    match: str = "match"


