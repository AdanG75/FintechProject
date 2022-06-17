
import os
from typing import Optional, Tuple, Union

from cryptography.hazmat.primitives import padding as symmetric_padding
from cryptography.hazmat.primitives.ciphers import algorithms, modes
from cryptography.hazmat.primitives.ciphers import Cipher as Cipher_AES
from cryptography.hazmat.primitives.ciphers.base import Cipher
from cryptography.hazmat.primitives.ciphers.modes import Mode

from core import utils


def generate_secret_key(length: int) -> bytes:
    """
    AES algorithm

    Generate a key to AES algorithm
    :param length: (int) - Length of the key to generate. Only can be the next values: 128, 192 or 256
    :return: (bytes) - A key to AES algorithm
    """
    possible_len_key = (128, 192, 256)

    if length in possible_len_key:
        key = os.urandom(int(length / 8))
    else:
        raise ValueError("The length would be 128, 192 or 256")

    return key


def generate_initialization_vector(length: int) -> bytes:
    """
    AES algorithm

    Generate an initialization vector. Must be the same number of bytes as the block_size of the cipher.
    Generally its size is half the size of the key.
    :param length: (int) - Length of initialization vector.
    :return: (bytes) - The initialization vector
    """
    iv = os.urandom(int(length / 8))

    return iv


def get_cipher(key_length: int) -> Tuple[bytes, bytes, int, Cipher[Optional[Mode]]]:
    """
    AES algorithm

    Create a cipher object using AES algorithm and CBC mode.
    In the same way, generate a key necessary to encrypt and decrypt data.
    Finally, the block size that use this AES algorithm is always 128.

    :param key_length: (int) - Length of the key to generate. Only can be the next values: 128, 192 or 256
    :return: Key of AES algorithm, the initialization vector, the block size of the algorithm and a Cipher object.
    """
    key = generate_secret_key(key_length)
    block_size: int = 128
    iv = generate_initialization_vector(block_size)

    cipher = Cipher_AES(algorithms.AES(key), modes.CBC(iv))

    return (key, iv, block_size, cipher)


def generate_cipher(key: Union[str, bytes], iv: Union[str, bytes]) -> Cipher[Optional[Mode]]:
    """
    AES algorithm

    Create a cipher object using AES algorithm and CBC mode.

    :param key: (Union[str, bytes]) - The key value. If it is passed as str, it would be in Base64 encoding.
    :param iv: (Union[str, bytes]) - The initialization vector value. If it is passed as str, it would be in Base64 encoding.
    :return: (Cipher[Optional[Mode]]) - An AES Cipher object.
    """
    secret_key = utils.get_bytes(key)
    iv_secret = utils.get_bytes(iv)

    cipher = Cipher_AES(algorithms.AES(secret_key), modes.CBC(iv_secret))

    return cipher


def AES_encrypt(message: Union[bytes, str], block_size: int, cipher: Cipher[Optional[Mode]]) -> bytes:
    """
    AES algorithm

    Encrypt a message using AES algorithm.

    :param message: (Union[bytes, str]) - Message to be encrypted.
    :param block_size: (int) - Size of each encryption block.
    :param cipher: (Cipher[Optional[Mode]]) - Cipher object.
    :return: (bytes) - An encrypted message.
    """
    message_bytes = bytes(message, 'utf-8') if isinstance(message, str) else message

    encryptor = cipher.encryptor()
    padder = symmetric_padding.PKCS7(block_size).padder()

    padded_data = padder.update(message_bytes) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    return encrypted_data


def AES_decrypt(encrypted_message: Union[bytes, str], block_size: int, cipher: Cipher[Optional[Mode]]) -> bytes:
    """
    AES algorithm

    Decrypt a message using AES algorithm.
    :param encrypted_message: (Union[bytes, str]) - Message to be decrypted.
        If it is passed as str, it would be in Base64 encoding.
    :param block_size: (int) - Size of each encryption block.
    :param cipher: (Cipher[Optional[Mode]]) - Cipher object.
    :return: (bytes) - A decrypted message.
    """
    message_bytes = utils.get_bytes(encrypted_message)

    decryptor = cipher.decryptor()
    padded_plain_text = decryptor.update(message_bytes) + decryptor.finalize()
    unpadder = symmetric_padding.PKCS7(block_size).unpadder()

    plain_text = unpadder.update(padded_plain_text) + unpadder.finalize()

    return plain_text