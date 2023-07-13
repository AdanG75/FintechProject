from enum import Enum


class TypeMovement(Enum):
    deposit = 'deposit'
    payment = 'payment'
    transfer = 'transfer'
    withdraw = 'withdraw'


class NatureMovement(Enum):
    income = 'income'
    outgoings = 'outgoings'
