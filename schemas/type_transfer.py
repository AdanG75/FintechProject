from enum import Enum


class TypeTransfer(Enum):
    local_to_local = 'localL'
    local_to_global = 'localG'
    global_to_local = 'globalL'
    global_to_global = 'globalG'
    default = 'paypal'
