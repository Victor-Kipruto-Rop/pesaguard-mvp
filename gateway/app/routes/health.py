"""Unauthenticated probe endpoints for load balancers and orchestrators."""
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.constants import HEALTH_PATH, LIVE_PATH, METRICS_PATH, READY_PATH
from app.health import ReadyProbeCache, collect_service_dependencies
from app.health.probes import status_summary

router = APIRouter(tags=["Operations"])


@router.get(HEALTH_PATH)
async def health(request: Request) -> dict[str, Any]:
    return {"status": "ok", "service": "gateway", "version": request.app.state.settings.version}


@router.get(LIVE_PATH)
async def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get(READY_PATH)
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
            cache = ReadyProbeCache()
            request.app.state.ready_probe_cache = cache

        service_dependencies, healthy_dependencies = await collect_service_dependencies(request, settings, cache)
        dependencies.update(service_dependencies)
        healthy = healthy and healthy_dependencies

    dependency_summary = {
        name: value if isinstance(value, str) else {"status": status_summary(value["status"]), "detail": value["detail"]}
        for name, value in dependencies.items()
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if healthy else "not_ready",
            "dependencies": dependency_summary,
            "environment": settings.environment,
            "version": settings.version,
        },
    )


@router.get(METRICS_PATH, include_in_schema=False)
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
