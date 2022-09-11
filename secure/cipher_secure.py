import json
from typing import Dict, Union

from core import utils
from core.config import settings
from schemas.secure_base import SecureBase
from secure import aes_secure, rsa_secure


def pack_and_encrypt_data(data: Union[Dict, str], public_key_pem: str) -> Dict:
    # Cats Dict or String to JSON Object
    data_json_2 = json.dumps(data, indent=4, ensure_ascii=False)
    data_json_str = data_json_2.encode('utf-8')

    # Generate AES key and AES data
    key, iv, block_size, cipher = aes_secure.get_cipher(128)
    key_b64 = utils.cast_bytes_to_base64(key)
    iv_b64 = utils.cast_bytes_to_base64(iv)

    # Cipher data using AES key and convert it to base64
    cipher_data_bytes = aes_secure.AES_encrypt(data_json_str, block_size, cipher)
    cipher_data_b64 = utils.cast_bytes_to_base64(cipher_data_bytes)

    # Pack secure data
    json_secure = {
        "key": key_b64,
        "iv": iv_b64,
        "block_size": block_size
    }
    json_secure_2 = json.dumps(json_secure, indent=4, ensure_ascii=False)
    json_secure_str = json_secure_2.encode('utf-8')

    # Get RSA public key
    # with open("./fintech75_api/secure/kotlin_public_key.pem", "r") as pem:
    #     public_key_pem = pem.read()

    public_key = rsa_secure.get_public_key_from_pem(public_key_pem)

    # Cipher secure data
    secure_bytes = rsa_secure.encrypt_data(public_key, json_secure_str)
    secure_b64 = utils.cast_bytes_to_base64(secure_bytes)

    # Packet data to send
    json_send = {
        "data": cipher_data_b64,
        "secure": secure_b64
    }

    return json_send


def unpack_and_decrypt_data(data: Union[Dict, SecureBase]) -> Dict:
    data_dict: dict = data.dict() if isinstance(data, SecureBase) else data

    # Unpack data
    receive_encrypted_data = data_dict["data"]
    receive_secure = data_dict["secure"]

    # Load private key
    private_key_pem = settings.get_server_private_key()
    # with open("./fintech75_api/secure/private_key.pem", "r") as pem:
    #     private_key_pem = pem.read()

    private_key = rsa_secure.get_private_key_from_pem(private_key_pem)

    # Decrypt secure data from Json
    receive_secure_bytes = utils.cast_base64_to_bytes(receive_secure)
    decrypt_secure_bytes = rsa_secure.decrypt_data(private_key, receive_secure_bytes)
    decrypt_secure_json = json.loads(decrypt_secure_bytes.decode('utf-8'))

    # Unpack secure
    aes_key = decrypt_secure_json["key"]
    iv_decrypt = decrypt_secure_json["iv"]
    block_size_decrypt = int(decrypt_secure_json["block_size"])

    # Decrypt data
    aes_cipher = aes_secure.generate_cipher(aes_key, iv_decrypt)
    message_bytes = aes_secure.AES_decrypt(receive_encrypted_data, block_size_decrypt, aes_cipher)

    # Cast to Dict
    receive_data: Dict = json.loads(message_bytes.decode('utf-8'))

    return receive_data


def decrypt_data(msg: Union[bytes, str], return_mode: str = 'plain') -> Union[str, dict]:
    """
    Decipher the passed message using the system private key
    :param msg: (bytes, str) Whatever data which was ciphered with the system public key
    :param return_mode: (str) Indicates what type of data is to be returned.
    It can be a **dict** if you select 'json' or 'dict' or a **str** if you select 'plain'
    :return: (dict, str) Return a dict or a str depending on what has been selected
    """

    # Load private key
    private_key_pem = settings.get_server_private_key()
    private_key = rsa_secure.get_private_key_from_pem(private_key_pem)

    # Decrypt message
    receive_secure_bytes = utils.cast_base64_to_bytes(msg)
    decrypt_secure_bytes = rsa_secure.decrypt_data(private_key, receive_secure_bytes)

    if return_mode == 'json' or return_mode == 'dict':
        decrypt_secure_to_return = json.loads(decrypt_secure_bytes.decode('utf-8'))
    else:
        decrypt_secure_to_return = decrypt_secure_bytes.decode('utf-8')

    return decrypt_secure_to_return


def cipher_data(msg: Union[bytes, str]) -> str:
    # get server's secure items
    cipher_server_key = settings.get_server_cipher_key()
    server_iv = settings.get_server_iv()
    server_block_size = settings.get_server_block_size()

    # Cipher data using AES key and convert it to base64
    cipher = aes_secure.generate_cipher(cipher_server_key, server_iv)
    cipher_data_bytes = aes_secure.AES_encrypt(msg, server_block_size, cipher)
    cipher_data_b64 = utils.cast_bytes_to_base64(cipher_data_bytes)

    return cipher_data_b64


def decipher_data(data: Union[bytes, str]) -> str:
    # get server's secure items
    cipher_server_key = settings.get_server_cipher_key()
    server_iv = settings.get_server_iv()
    server_block_size = settings.get_server_block_size()

    # Decipher data using AES key and return it as str in utf-8
    cipher = aes_secure.generate_cipher(cipher_server_key, server_iv)
    data_bytes = aes_secure.AES_decrypt(data, server_block_size, cipher)

    return data_bytes.decode('utf-8')








