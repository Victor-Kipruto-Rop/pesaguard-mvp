"""Readiness probe utilities and caching helpers for the gateway health package."""
from __future__ import annotations

import time
from typing import Any

from fastapi import Request

from app.clients.service_client import ServiceClientConnectionError, ServiceClientTimeout


class ReadyProbeCache:
    """Simple TTL cache for dependency readiness results."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[str, float]] = {}

    def get(self, key: str, ttl: int) -> str | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        status_value, created = entry
        if ttl > 0 and time.monotonic() - created >= ttl:
            return None
        return status_value

    def set(self, key: str, status_value: str) -> None:
        self._entries[key] = (status_value, time.monotonic())

    @staticmethod
    def cache_key(service: str, settings: Any) -> str:
        return f"{settings.environment}:{settings.version}:{service}"


def _status_is_healthy(status_value: str, environment: str) -> bool:
    if status_value == "ok":
        return True
    if status_value == "not_discovered":
        return environment != "production"
    if status_value.startswith("unhealthy:") or status_value == "unavailable":
        return False
    return False


def status_summary(status_value: str) -> str:
    if status_value == "ok":
        return "healthy"
    if status_value == "not_discovered":
        return "not_discovered"
    if status_value.startswith("unhealthy:"):
        return "degraded"
    if status_value == "unavailable":
        return "unavailable"
    return "unknown"


async def probe_service_health(request: Request, service: str, settings: Any) -> str:
    upstream = settings.upstream_for(service)
    if not upstream:
        return "not_discovered"

    try:
        health_response = await request.app.state.service_client.request(
            settings.service_health_method(service),
            f"{upstream.rstrip('/')}{settings.service_health_path(service)}",
            raise_for_status=False,
            timeout=settings.upstream_timeout_seconds,
            trace_id=getattr(getattr(request, "state", None), "trace_id", None),
        )
        if 200 <= health_response.status_code < 300:
            return "ok"
        return f"unhealthy:{health_response.status_code}"
    except (ServiceClientTimeout, ServiceClientConnectionError):
        return "unavailable"
    except Exception:
        return "unavailable"


async def collect_service_dependencies(
    request: Request, settings: Any, cache: ReadyProbeCache
) -> tuple[dict[str, str], bool]:
    dependencies: dict[str, str] = {}
    healthy = True
    ttl = settings.service_health_cache_seconds

    for service in settings.route_services():
        cache_key = ReadyProbeCache.cache_key(service, settings)
        status_value = cache.get(cache_key, ttl)
        if status_value is None:
            status_value = await probe_service_health(request, service, settings)
            cache.set(cache_key, status_value)

        dependencies[f"service:{service}"] = status_value
        if not _status_is_healthy(status_value, settings.environment):
            healthy = False

    return dependencies, healthy
