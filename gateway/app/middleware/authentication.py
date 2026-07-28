"""Authenticate public API calls before a downstream service is selected."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.security import verify_api_key, verify_token
from app.core.audit import emit


PUBLIC_PATHS = {"/health", "/ready", "/live", "/metrics", "/docs", "/redoc", "/openapi.json"}
PUBLIC_AUTH_ROUTES = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/forgot-password"),
    ("POST", "/api/v1/auth/password/reset/request"),
    ("POST", "/api/v1/auth/password/reset/confirm"),
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS or (request.method, request.url.path) in PUBLIC_AUTH_ROUTES:
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        try:
            authorization = request.headers.get("authorization", "")
            if authorization.lower().startswith("bearer "):
                request.state.principal = await verify_token(
                    authorization[7:].strip(),
                    request.app.state.settings,
                    request.app.state.service_client,
                    request.app.state.jwks_cache,
                )
            elif api_key := request.headers.get("x-api-key"):
                request.state.principal = verify_api_key(api_key, request.app.state.settings)
            else:
                raise ValueError("credentials are required")
        except ValueError:
            emit("authentication", request_id=getattr(request.state, "request_id", None), outcome="denied", path=request.url.path)
            return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHENTICATED", "message": "Valid bearer token or API key required"}},
                                headers={"WWW-Authenticate": "Bearer"})
        emit("authentication", request_id=getattr(request.state, "request_id", None), subject=request.state.principal.subject,
             outcome="allowed", scheme=request.state.principal.auth_scheme)
        return await call_next(request)
