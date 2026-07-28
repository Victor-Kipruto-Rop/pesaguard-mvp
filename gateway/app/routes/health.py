"""Unauthenticated probe endpoints for load balancers and orchestrators."""
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["Operations"])


def _probe_cache_key(service: str, settings: Any) -> tuple[str, str, str]:
    return (service, settings.environment, settings.version)


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    return {"status": "ok", "service": "gateway", "version": request.app.state.settings.version}


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    dependencies: dict[str, str] = {}
    healthy = True
    if request.app.state.redis:
        try:
            await request.app.state.redis.ping()
            dependencies["redis"] = "ok"
            dependencies["rate_limit"] = "redis"
        except Exception:
            dependencies["redis"] = "unavailable"
            if settings.rate_limit_fail_open or settings.environment != "production":
                dependencies["rate_limit"] = "local_fallback"
            else:
                dependencies["rate_limit"] = "unavailable"
                healthy = False
    else:
        dependencies["redis"] = "not_configured"
        if settings.environment == "production" and not settings.rate_limit_fail_open:
            dependencies["rate_limit"] = "unavailable"
            healthy = False
        else:
            dependencies["rate_limit"] = "local_fallback"
    if request.app.state.db_engine:
        try:
            from sqlalchemy import text
            async with request.app.state.db_engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            dependencies["database"] = "ok"
        except Exception:
            dependencies["database"] = "unavailable"
            healthy = False

    if settings.route_config:
        cache = getattr(request.app.state, "ready_probe_cache", None)
        if cache is None:
            cache = {}
            request.app.state.ready_probe_cache = cache

        for service in settings.route_services():
            cache_key = _probe_cache_key(service, settings)
            cached_status = cache.get(cache_key)
            if cached_status is not None:
                dependencies[f"service:{service}"] = cached_status
                if cached_status != "ok":
                    healthy = False
                continue

            upstream = settings.upstream_for(service)
            if not upstream:
                dependencies[f"service:{service}"] = "not_discovered"
                if settings.environment == "production":
                    healthy = False
                cache[cache_key] = dependencies[f"service:{service}"]
                continue
            try:
                health_response = await request.app.state.service_client.request(
                    settings.service_health_method(service),
                    f"{upstream}{settings.service_health_path(service)}",
                    raise_for_status=False,
                    timeout=settings.upstream_timeout_seconds,
                )
                if 200 <= health_response.status_code < 300:
                    dependencies[f"service:{service}"] = "ok"
                    cache[cache_key] = "ok"
                else:
                    dependencies[f"service:{service}"] = f"unhealthy:{health_response.status_code}"
                    cache[cache_key] = dependencies[f"service:{service}"]
                    healthy = False
            except Exception:
                dependencies[f"service:{service}"] = "unavailable"
                cache[cache_key] = dependencies[f"service:{service}"]
                healthy = False

    return JSONResponse(status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
                        content={"status": "ready" if healthy else "not_ready", "dependencies": dependencies})


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
