from enum import Enum


class FingerprintType(Enum):
    authentication: str = "auth"
    test: str = "test"
    match: str = "match"


class TypeCore(Enum):
    delta: str = 'd'
    loop: str = 'l'
    whorl: str = 'w'


class TypeMinutia(Enum):
    bifurcation: str = 'b'
    end: str = 'e'


class TypeChPoint(Enum):
    bifurcation: str = 'b'
    end: str = 'e'
    delta: str = 'd'
    loop: str = 'l'
    whorl: str = 'w'
