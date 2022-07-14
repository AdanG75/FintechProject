import unittest

from core.config import settings
from core.utils import cast_bytes_to_base64
from secure import aes_secure


class TestServerCipherKey(unittest.TestCase):

    def test_secret_message(self):
        message = "Hola, como andan"

        cipher = aes_secure.generate_cipher(
            settings.get_server_cipher_key(),
            settings.get_server_iv()
        )

        secret_message = aes_secure.AES_encrypt(
            message,
            settings.get_server_block_size(),
            cipher
        )
        secret_message_b64 = cast_bytes_to_base64(secret_message)
        self.assertEqual(
            'fYziW9Vmitqk3EF4AmaCtpJjldN/1aVlk8x9mYjg8m4=',
            secret_message_b64,
            'Secret message is different'
        )

    def test_receive_message(self):
        message = "Hola, como andan"

        cipher = aes_secure.generate_cipher(
            settings.get_server_cipher_key(),
            settings.get_server_iv()
        )

        secret_message = aes_secure.AES_encrypt(
            message,
            settings.get_server_block_size(),
            cipher
        )
        secret_message_b64 = cast_bytes_to_base64(secret_message)

        receive_message = aes_secure.AES_decrypt(
            secret_message_b64,
            settings.get_server_block_size(),
            cipher
        )
        self.assertEqual(
            message,
            receive_message.decode('utf-8'),
            'Receive message should be \'Hola, como andan\''
        )




