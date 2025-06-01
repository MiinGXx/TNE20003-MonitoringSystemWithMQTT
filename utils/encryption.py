from cryptography.fernet import Fernet
import os

class EncryptionManager:
    """
    EncryptionManager provides symmetric encryption and decryption functionality using Fernet.
    Attributes:
        key (bytes): The encryption key used for encrypting and decrypting messages.
        cipher_suite (Fernet): The Fernet cipher suite initialized with the encryption key.
    Methods:
        __init__():
            Initializes the EncryptionManager by generating or loading an encryption key and setting up the cipher suite.
        _get_or_create_key():
            Generates a new encryption key and saves it to a file if it does not exist, or loads the existing key from file.
            Returns:
                bytes: The encryption key.
        encrypt(message: str) -> bytes:
            Encrypts a plaintext string message.
            Args:
                message (str): The plaintext message to encrypt.
            Returns:
                bytes: The encrypted message as bytes.
        decrypt(encrypted_message: bytes) -> str:
            Decrypts an encrypted message.
            Args:
                encrypted_message (bytes): The encrypted message to decrypt.
            Returns:
                str: The decrypted plaintext message.
    """
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
