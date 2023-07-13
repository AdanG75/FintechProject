from enum import Enum


class TypeAuthMovement(Enum):
    local = 'LOCAL'
    paypal = 'PAYPAL'
    localPaypal = 'LOCAL-PAYPAL'
    without = 'WITHOUT'


class TypeAuthFrom(Enum):
    fingerprint = 'fingerprint'
    paypal = 'paypal'
    without = 'without'
