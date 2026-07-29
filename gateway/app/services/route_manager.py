"""Gateway service orchestration helpers used by the proxy and health packages."""
from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.constants import normalize_route_path


class RouteManager:
    """Centralized gateway route and upstream URL orchestration."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def service_names(self) -> tuple[str, ...]:
        return self.settings.route_services()

    def service_exists(self, service: str) -> bool:
        return service in self.service_names()

    def resolve_service_url(self, service: str) -> str | None:
        return self.settings.upstream_for(service)

    def gateway_route(self, service: str) -> str:
        return normalize_route_path(self.settings.gateway_path_for(service) or f"/{service}")

    def service_path_prefix(self, service: str) -> str:
        return self.settings.path_prefix_for(service) or f"/{service}"

    def build_upstream_url(self, service: str, path: str = "") -> str:
        upstream = self.resolve_service_url(service)
        if not upstream:
            raise ValueError(f"unable to resolve upstream URL for service {service}")

        prefix = self.service_path_prefix(service)
        if "{service}" in prefix:
            upstream_path = prefix.format(service=service)
        else:
            upstream_path = f"{prefix.rstrip('/')}/{service}" if prefix != "/" else f"/{service}"

        if path:
            normalized_path = path.lstrip("/")
            return f"{upstream.rstrip('/')}{upstream_path.rstrip('/')}/{normalized_path}"

        return f"{upstream.rstrip('/')}{upstream_path.rstrip('/')}"

    def service_metadata(self, service: str) -> dict[str, Any]:
        return {
            "service": service,
            "gateway_path": self.gateway_route(service),
            "upstream_url": self.resolve_service_url(service),
            "methods": self.settings.supported_methods_for(service) or tuple(),
            "health_path": self.settings.service_health_path(service),
            "health_method": self.settings.service_health_method(service),
        }
