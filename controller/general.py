from typing import Union

from db.orm.exceptions_orm import type_of_value_not_compatible, bad_cipher_data_exception
from schemas.secure_base import SecureBase
from secure.cipher_secure import unpack_and_decrypt_data, decrypt_data


def get_data_from_secure(request: SecureBase) -> dict:
    if isinstance(request, SecureBase):
        try:
            receive_data = unpack_and_decrypt_data(request.dict())
        except ValueError:
            raise bad_cipher_data_exception
        # print(receive_data)
    else:
        raise type_of_value_not_compatible

    return receive_data


def get_data_from_rsa_message(msg: Union[str, bytes]) -> Union[str, dict]:
    try:
        decipher_msg = decrypt_data(msg)
    except ValueError:
        raise bad_cipher_data_exception

    return decipher_msg
