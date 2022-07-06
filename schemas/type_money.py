from enum import Enum


class TypeMoney(Enum):
    local = 'local'
    paypal = 'paypal'
    cash = 'cash'
    card = 'card'
    globalC = 'global'
