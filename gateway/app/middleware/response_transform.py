"""Middleware that applies route-specific response rewriting and cache control."""
from __future__ import annotations

from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.constants import DEFAULT_API_PREFIX


class ResponseTransformMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        service = self._service_for_request(request)
        if service and request.app.state.settings.route_config:
            settings = request.app.state.settings
            cache_control = settings.cache_control_for(service)
            if cache_control:
                response.headers["Cache-Control"] = cache_control
            response_headers = settings.response_headers_for(service)
            for key, value in response_headers.items():
                response.headers[key] = value

            rewrite = settings.response_body_rewrite_for(service)
            if rewrite and hasattr(response, "body"):
                response.body = rewrite.encode("utf-8")
                response.headers["Content-Length"] = str(len(response.body))

        return response

    @staticmethod
    def _service_for_request(request: Request) -> str | None:
        route = request.scope.get("route")
        if route is not None:
            name = getattr(route, "name", "") or ""
            if name:
                return name.replace("proxy_", "").replace("proxy_websocket_", "") or None

        settings = getattr(request.app.state, "settings", None)
        if not settings or not settings.route_config:
            return None

        path = request.url.path.rstrip("/") or "/"
        candidates = []
        for service in settings.route_services():
            gateway_path = settings.gateway_path_for(service) or f"/{service}"
            gateway_path = gateway_path.rstrip("/") or "/"
            candidates.append(gateway_path)
            prefixed_path = f"{DEFAULT_API_PREFIX}{gateway_path}" if not gateway_path.startswith(DEFAULT_API_PREFIX) else gateway_path
            candidates.append(prefixed_path)

        for service_name in settings.route_services():
            gateway_path = settings.gateway_path_for(service_name) or f"/{service_name}"
            gateway_path = gateway_path.rstrip("/") or "/"
            prefixed_path = f"{DEFAULT_API_PREFIX}{gateway_path}" if not gateway_path.startswith(DEFAULT_API_PREFIX) else gateway_path
            if path == gateway_path or path.startswith(f"{gateway_path}/") or path == prefixed_path or path.startswith(f"{prefixed_path}/"):
                return service_name
        return None
