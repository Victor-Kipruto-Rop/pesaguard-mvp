"""Network and response-hardening controls."""
from ipaddress import ip_address, ip_network

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = request.app.state.settings
        from app.core.client_ip import client_ip
        client = client_ip(request)
        if self._matches(client, settings.denied_ips) or (settings.allowed_ips and not self._matches(client, settings.allowed_ips)):
            return JSONResponse(status_code=403, content={"error": {"code": "IP_NOT_ALLOWED", "message": "Client IP is not permitted"}})
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.request_max_bytes:
            return JSONResponse(status_code=413, content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds limit"}})
        if request.method in {"POST", "PUT", "PATCH"} and request.url.path.startswith("/api/"):
            media_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
            if media_type and not any(media_type == allowed or media_type.startswith(f"{allowed}/") for allowed in settings.allowed_content_types):
                return JSONResponse(status_code=415, content={"error": {"code": "UNSUPPORTED_MEDIA_TYPE", "message": "Request content type is not allowed"}})
            if len(await request.body()) > settings.request_max_bytes:
                return JSONResponse(status_code=413, content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds limit"}})
        response = await call_next(request)
        response.headers.update({
            "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()", "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        })
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @staticmethod
    def _matches(value: str, rules: list[str]) -> bool:
        try:
            return any(ip_address(value) in ip_network(rule, strict=False) for rule in rules)
        except ValueError:
            return False
