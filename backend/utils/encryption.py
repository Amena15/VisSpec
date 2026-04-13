"""
AES-256 encryption utility for data-at-rest protection.
Uses the cryptography library for authenticated encryption (AES-GCM).
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key() -> bytes:
    """Generate a new 256-bit AES key."""
    return AESGCM.generate_key(bit_length=256)


def key_to_base64(key: bytes) -> str:
    """Convert raw key bytes to base64 string for storage."""
    return base64.b64encode(key).decode("utf-8")


def key_from_base64(key_b64: str) -> bytes:
    """Restore raw key bytes from base64 string."""
    return base64.b64decode(key_b64)


class AESEncryptor:
    """AES-256-GCM encryptor for sensitive data."""

    def __init__(self, key: bytes):
        self.aesgcm = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value. Returns base64(nonce + ciphertext).
        """
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a base64(nonce + ciphertext) string.
        """
        raw = base64.b64decode(encrypted_data)
        nonce = raw[:12]
        ciphertext = raw[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
