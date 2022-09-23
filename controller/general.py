from typing import Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.utils import iter_object_to_become_serializable
from db.orm.exceptions_orm import type_of_value_not_compatible, bad_cipher_data_exception
from db.orm.users_orm import get_public_key_pem
from schemas.secure_base import SecureBase
from secure.cipher_secure import unpack_and_decrypt_data, decrypt_data, pack_and_encrypt_data


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


def cipher_response_message(db: Session, id_user: int, response: Union[BaseModel, dict]) -> SecureBase:
    """
    Pack and cipher the response to send

    :param db: (Session) An instance of the database
    :param id_user: (int) The user's id who we will send the response
    :param response: (BaseModel, dict) The unsecure response to send
    :return: (SecureBase) A secure response
    """
    # Check that all values are serializable within the dict
    dict_response = response.dict().copy() if isinstance(response, BaseModel) else response
    iter_object_to_become_serializable(dict_response)

    # get public key of user
    public_key_pem = get_public_key_pem(db, id_user)

    # Pack and cipher response
    packed_response: dict = pack_and_encrypt_data(dict_response, public_key_pem)
    secure_base_response = SecureBase.parse_obj(packed_response)

    return secure_base_response
