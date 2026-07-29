"""Authenticate public API calls before a downstream service is selected."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.constants import AUTH_PUBLIC_ROUTES, PUBLIC_PATHS
from app.core.audit import emit
from app.core.security import verify_api_key, verify_token
from app.responses import error_response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if self._is_public_request(request):
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        try:
            principal = await self._authenticate(request)
        except ValueError as exc:
            emit(
                "authentication",
                request_id=getattr(request.state, "request_id", None),
                outcome="denied",
                path=request.url.path,
                reason=str(exc),
            )
            payload = error_response("UNAUTHENTICATED", "Valid bearer token or API key required")
            return JSONResponse(
                status_code=401,
                content=payload.model_dump(),
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.principal = principal
        request.state.auth_scheme = getattr(principal, "auth_scheme", "unknown")
        request.state.auth_context = {
            "scheme": request.state.auth_scheme,
            "subject": getattr(principal, "subject", None),
            "scopes": sorted(getattr(principal, "scopes", frozenset())),
            "path": request.url.path,
        }
        emit(
            "authentication",
            request_id=getattr(request.state, "request_id", None),
            subject=getattr(principal, "subject", None),
            outcome="allowed",
            scheme=request.state.auth_scheme,
            path=request.url.path,
        )
        return await call_next(request)

    @staticmethod
    def _is_public_request(request: Request) -> bool:
        return request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS or (request.method, request.url.path) in AUTH_PUBLIC_ROUTES

    async def _authenticate(self, request: Request):
        authorization = request.headers.get("authorization", "")
        if authorization and authorization.strip():
            scheme, _, value = authorization.partition(" ")
            normalized_scheme = scheme.lower()
            if normalized_scheme == "bearer" and value.strip():
                return await verify_token(
                    value.strip(),
                    request.app.state.settings,
                    getattr(request.app.state, "service_client", None),
                    getattr(request.app.state, "jwks_cache", None),
                )
            if normalized_scheme == "apikey" and value.strip():
                return verify_api_key(value.strip(), request.app.state.settings)
            raise ValueError("unsupported authorization scheme")

        api_key = request.headers.get("x-api-key")
        if api_key:
            return verify_api_key(api_key, request.app.state.settings)
        raise ValueError("credentials are required")
