"""Gateway service orchestration helpers used by the proxy and health packages."""
from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.constants import normalize_route_path


class RouteManager:
    """Centralized gateway route and upstream URL orchestration."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # state for weighted round-robin selection per service
        self._rr_counters: dict[str, int] = {}
        self._rr_totals: dict[str, int] = {}
        self._rr_urls_weights: dict[str, list[tuple[str, int]]] = {}

    def service_names(self) -> tuple[str, ...]:
        return self.settings.route_services()

    def service_exists(self, service: str) -> bool:
        return service in self.service_names()

    def resolve_service_url(self, service: str) -> str | None:
        # prefer weighted round-robin when multiple upstreams are configured
        try:
            if self.settings.route_config:
                upstream_defs = self.settings.route_config.upstream_definitions_for(service)
                if len(upstream_defs) > 1:
                    selected = self.select_upstream_round_robin(service)
                    if selected:
                        return selected
        except Exception:
            # fall back to existing upstream resolution logic
            pass

        return self.settings.upstream_for(service)

    def select_upstream_round_robin(self, service: str, env: dict[str, str] | None = None) -> str | None:
        """Select an upstream URL for a service using a weighted round-robin algorithm.

        This method is stateful: it keeps a simple counter per service to rotate
        selections proportionally to configured weights.
        """
        env = env or __import__("os").environ
        if not self.settings.route_config:
            return None

        # prepare cached url/weight tuples
        if service not in self._rr_urls_weights:
            upstream_defs = self.settings.route_config.upstream_definitions_for(service)
            available: list[tuple[str, int]] = []
            for upstream in upstream_defs:
                url = upstream.resolve_url(env)
                if url:
                    available.append((url.rstrip("/"), upstream.weight))
            if not available:
                return None
            total = sum(weight for _, weight in available)
            self._rr_urls_weights[service] = available
            self._rr_totals[service] = total
            self._rr_counters[service] = 0

        available = self._rr_urls_weights.get(service, [])
        total = self._rr_totals.get(service, 0)
        if not available or total <= 0:
            return None

        counter = self._rr_counters.get(service, 0)
        choice = counter % total
        # advance counter for next call
        self._rr_counters[service] = counter + 1

        # select based on accumulated weights
        acc = 0
        for url, weight in available:
            acc += weight
            if choice < acc:
                return url
        # fallback (shouldn't normally happen)
        return available[-1][0]

    async def select_healthy_upstream(self, service: str, service_client, env: dict[str, str] | None = None, visited: set[str] | None = None) -> str | None:
        """Select an upstream that responds successfully to the configured health check.

        Tries upstreams in weighted round-robin order and returns the first that the
        `service_client` reports as healthy. If none are healthy, attempts the
        configured fallback service (if any) once.
        """
        env = env or __import__("os").environ
        visited = visited or set()
        if service in visited:
            return None
        visited.add(service)

        if not self.settings.route_config:
            return None

        upstream_defs = self.settings.route_config.upstream_definitions_for(service)
        candidates: list[tuple[str, int]] = []
        for upstream in upstream_defs:
            url = upstream.resolve_url(env)
            if url:
                candidates.append((url.rstrip("/"), upstream.weight))

        if not candidates:
            # try fallback service
            fallback = self.settings.fallback_service_for(service)
            if fallback and fallback not in visited:
                return await self.select_healthy_upstream(fallback, service_client, env, visited)
            return None

        # build expanded list respecting weights
        expanded: list[str] = []
        for url, weight in candidates:
            expanded.extend([url] * max(1, weight))

        # start index based on round-robin counter
        idx = self._rr_counters.get(service, 0) % len(expanded)

        # attempt each candidate once
        timeout = min(2.0, float(getattr(self.settings, "upstream_timeout_seconds", 2.0)))
        for i in range(len(expanded)):
            candidate = expanded[(idx + i) % len(expanded)]
            # build health URL
            health_path = self.settings.service_health_path(service) or "/health"
            health_method = self.settings.service_health_method(service) or "GET"
            try:
                resp = await service_client.request(health_method, f"{candidate.rstrip('/')}{health_path}", timeout=timeout, raise_for_status=False)
                if resp is not None and getattr(resp, "status_code", 0) < 500:
                    # advance rr counter for next call
                    self._rr_counters[service] = self._rr_counters.get(service, 0) + 1
                    return candidate
            except Exception:
                # treat as unhealthy and continue
                continue

        # nothing healthy; try fallback service if configured
        fallback = self.settings.fallback_service_for(service)
        if fallback and fallback not in visited:
            return await self.select_healthy_upstream(fallback, service_client, env, visited)
        return None

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
