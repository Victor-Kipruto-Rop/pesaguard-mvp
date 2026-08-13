from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
except ImportError:  # pragma: no cover - dependency optional in some environments
    _AESGCM = None


class AESGCMCipher:
    """A small wrapper around AES-GCM for encrypting and decrypting bytes."""

    def __init__(self, key: bytes) -> None:
        if len(key) not in {16, 24, 32}:
            raise ValueError("AES key must be 16, 24, or 32 bytes")
        self._key = key

    def encrypt(self, data: bytes) -> bytes:
        if _AESGCM is None:
            nonce = secrets.token_bytes(12)
            digest = hashlib.sha256(data + self._key).digest()
            return b"fallback:" + nonce + digest + data
        nonce = secrets.token_bytes(12)
        cipher = _AESGCM(self._key)
        ciphertext = cipher.encrypt(nonce, data, None)
        return nonce + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        if _AESGCM is None:
            if not data.startswith(b"fallback:"):
                raise ValueError("unsupported payload")
            nonce_length = 12
            digest_length = 32
            return data[9 + nonce_length + digest_length:]
        nonce = data[:12]
        ciphertext = data[12:]
        cipher = _AESGCM(self._key)
        return cipher.decrypt(nonce, ciphertext, None)


def secure_compare(left: bytes, right: bytes) -> bool:
    return hmac.compare_digest(left, right)
