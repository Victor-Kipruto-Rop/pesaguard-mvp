"""Shared constants and normalized utility helpers for the gateway."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Final, FrozenSet, Iterable, Tuple

DEFAULT_API_PREFIX: Final[str] = "/api/v1"
HEALTH_PATH: Final[str] = "/health"
LIVE_PATH: Final[str] = "/live"
READY_PATH: Final[str] = "/ready"
METRICS_PATH: Final[str] = "/metrics"
DOCS_PATH: Final[str] = "/docs"
REDOC_PATH: Final[str] = "/redoc"
OPENAPI_PATH: Final[str] = "/openapi.json"

DEFAULT_HTTP_METHODS: Final[tuple[str, ...]] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD")

PUBLIC_PATHS: Final[FrozenSet[str]] = frozenset(
    {HEALTH_PATH, LIVE_PATH, READY_PATH, METRICS_PATH, DOCS_PATH, REDOC_PATH, OPENAPI_PATH}
)

PROBE_PATHS: Final[FrozenSet[str]] = frozenset({HEALTH_PATH, LIVE_PATH, READY_PATH, METRICS_PATH})

AUTH_PUBLIC_ROUTES: Final[FrozenSet[Tuple[str, str]]] = frozenset(
    {
        ("POST", f"{DEFAULT_API_PREFIX}/auth/register"),
        ("POST", f"{DEFAULT_API_PREFIX}/auth/login"),
        ("POST", f"{DEFAULT_API_PREFIX}/auth/refresh"),
        ("POST", f"{DEFAULT_API_PREFIX}/auth/forgot-password"),
        ("POST", f"{DEFAULT_API_PREFIX}/auth/password/reset/request"),
        ("POST", f"{DEFAULT_API_PREFIX}/auth/password/reset/confirm"),
    }
)

HOP_BY_HOP_HEADERS: Final[FrozenSet[str]] = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "host",
    }
)

SENSITIVE_HEADERS: Final[FrozenSet[str]] = frozenset(
    {
        "authorization",
        "x-api-key",
        "x-authenticated-subject",
        "x-authenticated-scopes",
    }
)

REQUEST_ID_HEADER: Final[str] = "X-Request-ID"
CORRELATION_ID_HEADER: Final[str] = "X-Correlation-ID"
AUTHENTICATED_SUBJECT_HEADER: Final[str] = "X-Authenticated-Subject"
AUTHENTICATED_SCOPES_HEADER: Final[str] = "X-Authenticated-Scopes"
AUTHORIZATION_HEADER: Final[str] = "Authorization"


def normalize_route_path(path: str) -> str:
    """Normalize a gateway route path to a single slash-delimited form."""
    normalized = "/".join(segment for segment in path.split("/") if segment)
    return f"/{normalized}" if normalized else "/"


@dataclass(frozen=True)
class GatewayRouteMetadata:
    api_prefix: str = DEFAULT_API_PREFIX
    health_path: str = HEALTH_PATH
    live_path: str = LIVE_PATH
    ready_path: str = READY_PATH
    metrics_path: str = METRICS_PATH
    docs_path: str = DOCS_PATH
    redoc_path: str = REDOC_PATH
    openapi_path: str = OPENAPI_PATH

    @property
    def public_paths(self) -> FrozenSet[str]:
        return PUBLIC_PATHS

    @property
    def probe_paths(self) -> FrozenSet[str]:
        return PROBE_PATHS

    def service_route(self, service: str) -> str:
        return normalize_route_path(f"{self.api_prefix}/{service}")


GATEWAY_ROUTES = GatewayRouteMetadata()
