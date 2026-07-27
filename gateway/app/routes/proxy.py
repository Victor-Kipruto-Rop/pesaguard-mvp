"""Service routing layer. Routes preserve method, body and approved request context."""
from collections.abc import Awaitable, Callable

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.exceptions.handlers import GatewayError

router = APIRouter(prefix="/api/v1", tags=["Gateway"])
SERVICE_PREFIXES = ("auth", "organizations", "merchants", "payments", "reconciliation", "notifications")
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "host"}


async def forward(service: str, path: str, request: Request) -> Response:
    upstream = request.app.state.settings.upstream_for(service)
    if not upstream:
        raise GatewayError(503, "SERVICE_UNAVAILABLE", f"{service} service is not configured")
    headers = {key: value for key, value in request.headers.items() if key.lower() not in HOP_BY_HOP}
    headers.update({"X-Request-ID": request.state.request_id, "X-Correlation-ID": request.state.correlation_id})
    principal = getattr(request.state, "principal", None)
    if principal:
        headers["X-Authenticated-Subject"] = principal.subject
        headers["X-Authenticated-Scopes"] = " ".join(sorted(principal.scopes))
    url = f"{upstream}/{path}" if path else upstream
    try:
        upstream_response = await request.app.state.http.request(
            request.method, url, params=request.query_params, content=await request.body(), headers=headers
        )
    except httpx.TimeoutException as exc:
        raise GatewayError(504, "UPSTREAM_TIMEOUT", f"{service} service timed out") from exc
    except httpx.HTTPError as exc:
        raise GatewayError(502, "UPSTREAM_UNAVAILABLE", f"{service} service could not be reached") from exc
    response_headers = {key: value for key, value in upstream_response.headers.items() if key.lower() not in HOP_BY_HOP}
    return Response(upstream_response.content, upstream_response.status_code, response_headers,
                    media_type=upstream_response.headers.get("content-type"))


@router.api_route("/{service}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(service: str, request: Request, path: str = "") -> Response:
    if service not in SERVICE_PREFIXES:
        raise GatewayError(404, "SERVICE_NOT_FOUND", "The requested API service does not exist")
    return await forward(service, path, request)
