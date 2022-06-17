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
    # with open("/home/coffe/Documentos/fintech75_api/secure/kotlin_public_key.pem", "r") as pem:
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
    # with open("/home/coffe/Documentos/fintech75_api/secure/private_key.pem", "r") as pem:
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




