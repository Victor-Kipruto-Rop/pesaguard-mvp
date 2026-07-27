"""Authentication primitives shared by middleware and dependencies."""
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from hmac import compare_digest
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.config.settings import Settings


@dataclass(frozen=True)
class Principal:
    subject: str
    scopes: frozenset[str]
    claims: dict[str, Any]
    auth_scheme: str


def verify_token(token: str, settings: Settings) -> Principal:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except InvalidTokenError as exc:
        raise ValueError("invalid bearer token") from exc
    scopes = claims.get("scope", "")
    return Principal(str(claims["sub"]), frozenset(scopes.split()), claims, "bearer")


def verify_api_key(api_key: str, settings: Settings) -> Principal:
    digest = sha256(api_key.encode()).hexdigest()
    if not any(compare_digest(digest, known) for known in settings.api_key_hashes):
        raise ValueError("invalid API key")
    return Principal(f"api-key:{digest[:12]}", frozenset({"gateway:access"}), {}, "api_key")


def issue_development_token(subject: str, settings: Settings) -> str:
    """Convenience helper for local tests; production identity is issued by auth service."""
    now = datetime.now(UTC)
    return jwt.encode({"sub": subject, "iat": now, "exp": now.timestamp() + 3600,
                       "aud": settings.jwt_audience, "iss": settings.jwt_issuer},
                      settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
