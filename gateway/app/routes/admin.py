"""Read-only gateway administration endpoints with no business-domain behavior."""
from fastapi import APIRouter, Request

from app.exceptions.handlers import GatewayError

router = APIRouter(prefix="/api/v1/gateway", tags=["Gateway administration"])


@router.get("/status")
async def gateway_status(request: Request) -> dict[str, object]:
    principal = getattr(request.state, "principal", None)
    if not principal or "gateway:admin" not in principal.scopes:
        raise GatewayError(403, "FORBIDDEN", "Gateway administration permission is required")
    settings = request.app.state.settings
    return {
        "service": "gateway",
        "environment": settings.environment,
        "configured_upstreams": sorted(service for service in settings.route_services() if settings.upstream_for(service)),
        "redis_configured": bool(settings.redis_url),
    }
