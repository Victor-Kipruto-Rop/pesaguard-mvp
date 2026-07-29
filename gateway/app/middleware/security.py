"""Network and response-hardening controls."""
from __future__ import annotations

from ipaddress import ip_address, ip_network

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.responses import error_response


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = getattr(getattr(request.app, "state", None), "settings", None)
        if settings is None:
            return await call_next(request)

        from app.core.client_ip import client_ip

        client = client_ip(request)
        request.state.client_ip = client
        request.state.security_context = {
            "client_ip": client,
            "allowed_ips": settings.allowed_ips,
            "denied_ips": settings.denied_ips,
        }
        if self._matches(client, settings.denied_ips) or (settings.allowed_ips and not self._matches(client, settings.allowed_ips)):
            payload = error_response("IP_NOT_ALLOWED", "Client IP is not permitted")
            return JSONResponse(status_code=403, content=payload.model_dump())

        content_length = self._parse_content_length(request.headers.get("content-length"))
        if content_length is not None and content_length > settings.request_max_bytes:
                payload = error_response("PAYLOAD_TOO_LARGE", "Request body exceeds limit")
                return JSONResponse(status_code=413, content=payload.model_dump())
        if request.method in {"POST", "PUT", "PATCH"} and request.url.path.startswith("/api/"):
            media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if media_type and not any(media_type == allowed or media_type.startswith(f"{allowed}/") for allowed in settings.allowed_content_types):
                payload = error_response("UNSUPPORTED_MEDIA_TYPE", "Request content type is not allowed")
                return JSONResponse(status_code=415, content=payload.model_dump())
            body = await request.body()
            if len(body) > settings.request_max_bytes:
                payload = error_response("PAYLOAD_TOO_LARGE", "Request body exceeds limit")
                return JSONResponse(status_code=413, content=payload.model_dump())

        response = await call_next(request)
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }
        for name, value in headers.items():
            response.headers.setdefault(name, value)
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @staticmethod
    def _matches(value: str, rules: list[str]) -> bool:
        try:
            return any(ip_address(value) in ip_network(rule, strict=False) for rule in rules)
        except ValueError:
            return False

    @staticmethod
    def _parse_content_length(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed
