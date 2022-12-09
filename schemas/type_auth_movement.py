from enum import Enum


class TypeAuthMovement(Enum):
    local = 'LOCAL'
    paypal = 'PAYPAL'
    localPaypal = 'LOCAL-PAYPAL'
