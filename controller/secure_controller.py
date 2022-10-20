from typing import Union, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.utils import iter_object_to_become_serializable
from db.orm.exceptions_orm import type_of_value_not_compatible, bad_cipher_data_exception, not_values_sent_exception, \
    wrong_public_pem_format_exception
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


def cipher_response_message(
        response: Union[BaseModel, dict],
        without_auth: bool = False,
        db: Optional[Session] = None,
        id_user: Optional[int] = None,
        user_pem: Optional[str] = None
) -> SecureBase:
    """
    Pack and cipher the response to send

    :param response: (BaseModel, dict) The unsecure response to cipher and pack
    :param without_auth: (Bool) True when we do not request the client access token to give access to the entrypoint
    :param db: (Optional[Session]) An instance of the database. Necessary when is required an access token by the
    entrypoint
    :param id_user: (Optional[int]) The user's id who we will send the response. Necessary when is
    required an access token by the entrypoint
    :param user_pem:  [Optional[str]) Public pem of user who require a secure response. Necessary when an access
    token is not required by the entrypoint

    :return: (SecureBase) A secure response
    """
    # Check that all values are serializable within the dict
    dict_response = response.dict().copy() if isinstance(response, BaseModel) else response
    iter_object_to_become_serializable(dict_response)

    # get public key of user
    if without_auth:
        if user_pem is None:
            raise not_values_sent_exception

        public_key_pem = user_pem
    else:
        if db is None or id_user is None:
            raise not_values_sent_exception

        public_key_pem = get_public_key_pem(db, id_user)

    # Pack and cipher response
    try:
        packed_response: dict = pack_and_encrypt_data(dict_response, public_key_pem)
    except ValueError:
        print(public_key_pem)
        raise wrong_public_pem_format_exception

    secure_base_response = SecureBase.parse_obj(packed_response)

    return secure_base_response
