from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class APIKeyRecord:
    key_id: str
    secret_hash: str
    metadata: dict[str, str] | None = None


class APIKeyManager:
    """Creates and validates API keys using HMAC-based hashing."""

    def __init__(self, secret_key: str) -> None:
        if not secret_key:
            raise ValueError("secret_key must not be empty")
        self.secret_key = secret_key

    def create_key(self, *, key_id: Optional[str] = None, metadata: Optional[dict[str, str]] = None) -> tuple[str, APIKeyRecord]:
        key_id = key_id or self._generate_id()
        secret = self._generate_secret()
        secret_hash = self._hash_secret(secret)
        record = APIKeyRecord(key_id=key_id, secret_hash=secret_hash, metadata=metadata)
        return f"{key_id}.{secret}", record

    def validate_key(self, api_key: str, record: APIKeyRecord) -> bool:
        if "." not in api_key:
            return False
        key_id, secret = api_key.split(".", 1)
        return key_id == record.key_id and hmac.compare_digest(self._hash_secret(secret), record.secret_hash)

    def _hash_secret(self, secret: str) -> str:
        return hmac.new(self.secret_key.encode("utf-8"), secret.encode("utf-8"), hashlib.sha256).hexdigest()

    def _generate_id(self) -> str:
        return "pk_" + secrets.token_hex(4)

    def _generate_secret(self) -> str:
        alphabet = string.ascii_letters + string.digits
        return "sk_" + "".join(secrets.choice(alphabet) for _ in range(24))
