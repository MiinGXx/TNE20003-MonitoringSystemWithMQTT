from cryptography.fernet import Fernet
import os

class EncryptionManager:
    def __init__(self):
        # Generate or load key
        self.key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.key)

    def _get_or_create_key(self):
        key_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "encryption.key")
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key

    def encrypt(self, message: str) -> bytes:
        return self.cipher_suite.encrypt(message.encode())

    def decrypt(self, encrypted_message: bytes) -> str:
        return self.cipher_suite.decrypt(encrypted_message).decode()
