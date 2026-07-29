"""Runtime-oriented gateway service orchestration helpers."""
from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.services.route_manager import RouteManager


class GatewayServiceManager:
    """Expose richer runtime information for health and admin endpoints."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.route_manager = RouteManager(settings)

    def runtime_snapshot(self) -> dict[str, Any]:
        services: list[dict[str, Any]] = []
        configured_upstreams: list[str] = []
        for service in self.route_manager.service_names():
            upstream_url = self.route_manager.resolve_service_url(service)
            configured = bool(upstream_url)
            if configured:
                configured_upstreams.append(service)
            services.append(
                {
                    "name": service,
                    "gateway_path": self.route_manager.gateway_route(service),
                    "configured": configured,
                    "upstream_url": upstream_url,
                    "methods": list(self.settings.supported_methods_for(service) or []),
                    "health_path": self.settings.service_health_path(service),
                    "health_method": self.settings.service_health_method(service),
                }
            )

        return {
            "service": "gateway",
            "environment": self.settings.environment,
            "route_count": len(services),
            "configured_upstreams": configured_upstreams,
            "redis_configured": bool(self.settings.redis_url),
            "services": services,
        }
