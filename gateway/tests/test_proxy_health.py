from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import Request
from starlette.responses import Response

from app.health.probes import ReadyProbeCache, _status_is_healthy, collect_service_dependencies, probe_service_health, status_summary
from app.routes.proxy import forward, proxy


class DummyResponse:
    def __init__(self, status_code=200, content=b"ok", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


@pytest.mark.asyncio
async def test_proxy_forwards_to_upstream_and_preserves_status():
    settings = SimpleNamespace(
        route_config=True,
        route_services=lambda: ("payments",),
        supported_methods_for=lambda service: ("GET", "POST"),
        upstream_for=lambda service: "https://payments.example.com",
        path_prefix_for=lambda service: "/internal",
        upstream_max_retries=1,
    )
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                settings=settings,
                service_client=SimpleNamespace(request=AsyncMock(return_value=DummyResponse(status_code=201))),
                circuit_breaker=SimpleNamespace(allow=lambda service: True, success=lambda service: None, failure=lambda service: None),
            )
        ),
        headers={},
        method="POST",
        state=SimpleNamespace(request_id="req-1", correlation_id="corr-1"),
        body=AsyncMock(return_value=b"{}"),
        query_params={},
        url=SimpleNamespace(path="/api/v1/payments"),
    )

    response = await forward("payments", "", request)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_proxy_requires_scope_for_authenticated_requests():
    settings = SimpleNamespace(route_config=True, route_services=lambda: ("payments",))
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(settings=settings)),
        method="GET",
        url=SimpleNamespace(path="/api/v1/payments"),
        state=SimpleNamespace(principal=SimpleNamespace(scopes=frozenset(), subject="user")),
    )

    with pytest.raises(Exception):
        await proxy("payments", request)


def test_probe_cache_ttl_and_status_mapping():
    cache = ReadyProbeCache()
    cache.set("svc", "ok")
    assert cache.get("svc", ttl=60) == "ok"
    assert _status_is_healthy("ok", "test") is True
    assert _status_is_healthy("unavailable", "test") is False
    assert _status_is_healthy("not_discovered", "production") is False
    assert status_summary("unhealthy:500") == "degraded"


@pytest.mark.asyncio
async def test_collect_dependencies_marks_unhealthy_services():
    settings = SimpleNamespace(
        environment="test",
        version="1",
        route_services=lambda: ("payments", "ledger"),
        service_health_cache_seconds=60,
        upstream_for=lambda service: "https://example.com",
        service_health_method=lambda service: "GET",
        service_health_path=lambda service: "/health",
        upstream_timeout_seconds=1.0,
    )
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                service_client=SimpleNamespace(request=AsyncMock(return_value=DummyResponse(status_code=500)))
            )
        )
    )
    cache = ReadyProbeCache()

    dependencies, healthy = await collect_service_dependencies(request, settings, cache)

    assert healthy is False
    assert dependencies["service:payments"] == "unhealthy:500"
    assert dependencies["service:ledger"] == "unhealthy:500"
