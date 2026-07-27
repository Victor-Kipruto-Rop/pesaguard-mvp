"""Network and response-hardening controls."""
from ipaddress import ip_address, ip_network

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = request.app.state.settings
        client = request.client.host if request.client else ""
        if self._matches(client, settings.denied_ips) or (settings.allowed_ips and not self._matches(client, settings.allowed_ips)):
            return JSONResponse(status_code=403, content={"error": {"code": "IP_NOT_ALLOWED", "message": "Client IP is not permitted"}})
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.request_max_bytes:
            return JSONResponse(status_code=413, content={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds limit"}})
        response = await call_next(request)
        response.headers.update({
            "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()", "Cache-Control": "no-store",
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
