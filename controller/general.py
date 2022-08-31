
from db.orm.exceptions_orm import type_of_value_not_compatible
from schemas.secure_base import SecureBase
from secure.cipher_secure import unpack_and_decrypt_data


def get_data_from_secure(request: SecureBase) -> dict:
    if isinstance(request, SecureBase):
        receive_data = unpack_and_decrypt_data(request.dict())
        print(receive_data)
    else:
        raise type_of_value_not_compatible

    return receive_data
