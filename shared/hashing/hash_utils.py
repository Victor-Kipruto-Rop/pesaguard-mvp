from __future__ import annotations

import hashlib
import hmac
import secrets


class PasswordHasher:
    """A deterministic password hasher using PBKDF2-HMAC with per-password salts."""

    def __init__(self, iterations: int = 200_000, hash_name: str = "sha256") -> None:
        self.iterations = iterations
        self.hash_name = hash_name

    def hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac(self.hash_name, password.encode("utf-8"), salt, self.iterations)
        return f"$pbkdf2${self.hash_name}${self.iterations}${salt.hex()}${derived.hex()}"

    def verify_password(self, password: str, encoded: str) -> bool:
        parts = encoded.split("$")
        if len(parts) != 6 or parts[1] != "pbkdf2":
            return False
        _, _, algorithm, iterations, salt_hex, derived_hex = parts
        iterations_value = int(iterations)
        salt = bytes.fromhex(salt_hex)
        derived = hashlib.pbkdf2_hmac(algorithm, password.encode("utf-8"), salt, iterations_value)
        return hmac.compare_digest(derived.hex(), derived_hex)
