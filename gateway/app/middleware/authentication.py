"""Authenticate public API calls before a downstream service is selected."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.security import verify_api_key, verify_token


PUBLIC_PATHS = {"/health", "/ready", "/live", "/metrics", "/docs", "/openapi.json"}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        try:
            authorization = request.headers.get("authorization", "")
            if authorization.lower().startswith("bearer "):
                request.state.principal = verify_token(authorization[7:].strip(), request.app.state.settings)
            elif api_key := request.headers.get("x-api-key"):
                request.state.principal = verify_api_key(api_key, request.app.state.settings)
            else:
                raise ValueError("credentials are required")
        except ValueError:
            return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHENTICATED", "message": "Valid bearer token or API key required"}},
                                headers={"WWW-Authenticate": "Bearer"})
        return await call_next(request)
