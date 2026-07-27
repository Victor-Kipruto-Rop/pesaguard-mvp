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


def _decode_token(token: str, key: Any, settings: Settings) -> Principal:
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except InvalidTokenError as exc:
        raise ValueError("invalid bearer token") from exc
    scopes = claims.get("scope", "")
    return Principal(str(claims["sub"]), frozenset(scopes.split()), claims, "bearer")


async def verify_token(token: str, settings: Settings, http_client: Any, jwks_cache: dict[str, Any]) -> Principal:
    """Verify local development tokens or issuer-published asymmetric JWTs."""
    if not settings.jwt_jwks_url:
        return _decode_token(token, settings.jwt_secret.get_secret_value(), settings)
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise ValueError("token is missing a key identifier")
        import time
        async def refresh_keys() -> None:
            response = await http_client.get(str(settings.jwt_jwks_url))
            response.raise_for_status()
            jwks_cache["keys"] = {item["kid"]: item for item in response.json().get("keys", []) if "kid" in item}
            jwks_cache["expires_at"] = time.monotonic() + settings.jwt_jwks_cache_seconds
        if time.monotonic() >= jwks_cache.get("expires_at", 0):
            await refresh_keys()
        key = jwks_cache.get("keys", {}).get(kid)
        if not key:
            await refresh_keys()  # key rotation can occur before the normal cache expiry.
            key = jwks_cache.get("keys", {}).get(kid)
        if not key:
            raise ValueError("token signing key is not recognized")
        return _decode_token(token, jwt.algorithms.RSAAlgorithm.from_jwk(key) if settings.jwt_algorithm == "RS256" else jwt.algorithms.ECAlgorithm.from_jwk(key), settings)
    except Exception as exc:
        raise ValueError("invalid bearer token") from exc


def verify_api_key(api_key: str, settings: Settings) -> Principal:
    digest = sha256(api_key.encode()).hexdigest()
    if not any(compare_digest(digest, known) for known in settings.api_key_hashes):
        raise ValueError("invalid API key")
    return Principal(f"api-key:{digest[:12]}", frozenset(settings.api_key_scopes.get(digest, [])), {}, "api_key")


def issue_development_token(subject: str, settings: Settings, scopes: list[str] | None = None) -> str:
    """Convenience helper for local tests; production identity is issued by auth service."""
    now = datetime.now(UTC)
    return jwt.encode({"sub": subject, "scope": " ".join(scopes or []), "iat": now, "exp": now.timestamp() + 3600,
                       "aud": settings.jwt_audience, "iss": settings.jwt_issuer},
                      settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
