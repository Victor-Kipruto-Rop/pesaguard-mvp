from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


class TokenExpiredError(Exception):
    """Raised when a JWT-like token is expired."""


class TokenInvalidError(Exception):
    """Raised when a JWT-like token cannot be validated."""


@dataclass(slots=True)
class TokenPayload:
    subject: str
    issued_at: int
    expires_at: int
    claims: Dict[str, Any]


class JWTProvider:
    """A compact JWT-like provider with deterministic signing and expiry support."""

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        if not secret_key:
            raise ValueError("secret_key must not be empty")
        self.secret_key = secret_key
        self.algorithm = algorithm

    def issue_token(self, subject: str, expires_in: int = 300, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        now = int(time.time())
        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + max(expires_in, 0),
            "claims": additional_claims or {},
        }
        encoded_header = self._b64url(json.dumps({"alg": self.algorithm, "typ": "JWT"}).encode("utf-8"))
        encoded_payload = self._b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        signature = self._sign(signing_input)
        return f"{encoded_header}.{encoded_payload}.{self._b64url(signature)}"

    def verify_token(self, token: str) -> Dict[str, Any]:
        if not token:
            raise TokenInvalidError("token is empty")

        parts = token.split(".")
        if len(parts) != 3:
            raise TokenInvalidError("token must have 3 parts")

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_signature = self._sign(signing_input)
        if not hmac.compare_digest(expected_signature, self._b64decode(signature_b64)):
            raise TokenInvalidError("token signature is invalid")

        payload = json.loads(self._b64decode(payload_b64).decode("utf-8"))
        claims = payload.get("claims", {}) or {}
        if isinstance(claims, dict):
            payload.update(claims)
        exp = int(payload.get("exp", 0))
        if int(time.time()) >= exp:
            raise TokenExpiredError("token has expired")
        return payload

    def _sign(self, data: bytes) -> bytes:
        return hmac.new(self.secret_key.encode("utf-8"), data, hashlib.sha256).digest()

    @staticmethod
    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64decode(data: str) -> bytes:
        pad = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + pad)
