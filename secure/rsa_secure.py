
from typing import Optional, Tuple, Union

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from core import utils


def generate_public_and_private_keys() -> Tuple[RSAPrivateKey, RSAPublicKey]:
    """
    RSA algorithm

    Generate a private key and public key with the algorithm RSA.
    :return: (Tuple[RSAPrivateKey, RSAPublicKey]) - The private RSA key and the public RSA key, in that order.
    """
    secret_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    return (secret_private_key, secret_private_key.public_key())


def private_key_to_pem(
        secret_private_key: RSAPrivateKey,
        password_key: Optional[Union[str, bytes]] = None
) -> bytes:
    """
        RSA algorithm

        Serialize the private key to PEM encoding using PKCS8 as format which allows for better encryption.
        :param secret_private_key: (RSAPrivateKey) - A RSA private key
        :param password_key: (Optional[Union[str, bytes]) - Password to encrypt the private key.
        Only will be passed if you want to encrypt the private key.
        :return: (Tuple[bytes, bytes]) - The private key in PEM encoding.
    """

    if password_key is None:
        private_key_pem = secret_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    else:
        password_key_as_bytes = password_key.encode('utf-8') if isinstance(password_key, str) else password_key

        private_key_pem = secret_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password_key_as_bytes)
        )

    return private_key_pem


def public_key_to_pem(expose_public_key: RSAPublicKey) -> bytes:
    """
    RSA algorithm

    Serialize the public key to PEM encoding using SubjectPublicKeyInfo as format
    which is the typical public key format. It consists of an algorithm identifier
    and the public key as a bit string.

    :param expose_public_key: (RSAPublicKey) - A RSA public key
    :return: (bytes) - The public key in PEM encoding.
    """
    public_key_pem = expose_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_key_pem


def get_keys_as_pem(
        secret_private_key: RSAPrivateKey,
        expose_public_key: RSAPublicKey,
        password_key: Optional[Union[str, bytes]] = None
) -> Tuple[bytes, bytes]:
    """
    RSA algorithm

    Serialize the private and public RSA key using PEM encoding.
    :param secret_private_key: (RSAPrivateKey) - A RSA private key
    :param expose_public_key: (RSAPublicKey) - A RSA public key
    :param password_key: (Optional[Union[str, bytes]) - Password to encrypt the private key.
    Only will be passed if you want to encrypt the private key.
    :return: (Tuple[bytes, bytes]) - The private and public key in PEM encoding, in that order.
    """
    private_key_pem = private_key_to_pem(secret_private_key, password_key)
    public_key_pem = public_key_to_pem(expose_public_key)

    return (private_key_pem, public_key_pem)


def get_private_and_public_pem_as_strings(
        secret_private_key: RSAPrivateKey,
        expose_public_key: RSAPublicKey,
        password_key: Optional[Union[str, bytes]] = None
) -> Tuple[str, str]:
    """
    RSA algorithm

    Serialize the private and public RSA key, in string type (str), using PEM encoding.

    :param secret_private_key: (RSAPrivateKey) - A RSA private key
    :param expose_public_key: (RSAPublicKey) - A RSA public key
    :param password_key: (Optional[Union[str, bytes]) - Password to encrypt the private key.
    Only will be passed if you want to encrypt the private key.
    :return: (Tuple[str, str]) - The private and public key, in string type, using PEM encoding.
    """
    (private_key_pem, public_key_pem) = get_keys_as_pem(secret_private_key, expose_public_key, password_key)

    return (private_key_pem.decode('utf-8'), public_key_pem.decode('utf-8'))


def cast_byte_pem_to_string(pem_to_cast: bytes) -> str:
    """
    Cast a PEM of type bytes (bytes) to string type (str).
    :param pem_to_cast: (bytes) - The PEM to cast.
    :return: (str) - The PEM in string format.
    """
    return pem_to_cast.decode('utf-8')


def get_private_key_from_pem(
        private_key_pem: Union[bytes, str],
        password_key: Optional[Union[str, bytes]] = None
) -> RSAPrivateKey:
    """
    RSA algorithm

    Obtain the RSA private key from a PEM object.

    :param private_key_pem: (Union[bytes, str]) - PEM of a private key.
    :param password_key: (Optional[Union[str, bytes]]) - Password to decrypt the private key.
        If it is passed as str, it would be in Base64 encoding.
    Only will be passed if the private key is encrypted.
    :return: (RSAPrivateKey) - A private key object
    """

    pem = bytes(private_key_pem, 'utf-8') if isinstance(private_key_pem, str) else private_key_pem
    password_key_as_bytes = utils.get_bytes(password_key)

    secret_private_key = serialization.load_pem_private_key(
        pem,
        password=password_key_as_bytes
    )

    return secret_private_key


def get_public_key_from_pem(public_key_pem: Union[bytes, str]) -> RSAPublicKey:
    """
    RSA algorithm

    Obtain the RSA public key from a PEM object.
    :param public_key_pem: (Union[bytes, str]) - PEM of a public key.
    :return: (RSAPublicKey) - A public key object
    """
    pem = bytes(public_key_pem, 'utf-8') if isinstance(public_key_pem, str) else public_key_pem

    exposed_public_key = serialization.load_pem_public_key(
        pem
    )

    return exposed_public_key


def encrypt_data(exposed_public_key: RSAPublicKey, message: Union[bytes, str]) -> bytes:
    """
    RSA algorithm

    Encrypt the data using the public key.
    :param exposed_public_key: (RSAPublicKey) - A RSA public key object.
    :param message: (Union[bytes, str]) - Message to be encrypted.
    :return: (bytes) - A cipher message.
    """
    message_in_bytes = bytes(message, 'utf-8') if isinstance(message, str) else message

    ciphertext = exposed_public_key.encrypt(
        message_in_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return ciphertext


def decrypt_data(
        secret_private_key: RSAPrivateKey,
        secret_message: Union[str, bytes]
) -> bytes:
    """
    RSA algorithm

    Decrypt the data using the private key.
    :param secret_private_key: (RSAPrivateKey) - A RSA private key object.
    :param secret_message: (Union[str, bytes]) - Message to be decrypted.
        If it is passed as str, it would be in Base64 encoding.
    :return: (bytes) - A decrypted message.
    """
    secret_bytes = utils.get_bytes(secret_message)

    plain_text = secret_private_key.decrypt(
        ciphertext=secret_bytes,
        padding=padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return plain_text
