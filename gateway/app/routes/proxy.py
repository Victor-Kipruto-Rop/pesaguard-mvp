"""Service routing layer. Routes preserve method, body and approved request context."""
import asyncio
import time

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.exceptions.handlers import GatewayError
from app.metrics import UPSTREAM_LATENCY, UPSTREAM_REQUESTS, UPSTREAM_RETRIES

router = APIRouter(prefix="/api/v1", tags=["Gateway"])
SERVICE_PREFIXES = ("auth", "organizations", "merchants", "payments", "transactions", "reconciliation", "notifications", "reports", "audit")
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "host"}
SENSITIVE_HEADERS = {"authorization", "x-api-key", "x-authenticated-subject", "x-authenticated-scopes"}
UPSTREAM_PATHS = {service: f"/api/v1/{service}" for service in SERVICE_PREFIXES}
def _required_scope(service: str, method: str) -> str:
    action = "read" if method in {"GET", "HEAD", "OPTIONS"} else "write"
    return f"{service}:{action}"


def _is_retryable(method: str, headers: dict[str, str]) -> bool:
    return method in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"} or "idempotency-key" in headers


async def forward(service: str, path: str, request: Request) -> Response:
    upstream = request.app.state.settings.upstream_for(service)
    if not upstream:
        raise GatewayError(503, "SERVICE_UNAVAILABLE", f"{service} service is not configured")
    breaker = request.app.state.circuit_breaker
    if not breaker.allow(service):
        raise GatewayError(503, "UPSTREAM_CIRCUIT_OPEN", f"{service} service is temporarily isolated")
    headers = {key: value for key, value in request.headers.items() if key.lower() not in HOP_BY_HOP | SENSITIVE_HEADERS}
    headers.update({"X-Request-ID": request.state.request_id, "X-Correlation-ID": request.state.correlation_id})
    principal = getattr(request.state, "principal", None)
    if principal:
        headers["X-Authenticated-Subject"] = principal.subject
        headers["X-Authenticated-Scopes"] = " ".join(sorted(principal.scopes))
    upstream_path = UPSTREAM_PATHS[service]
    url = f"{upstream}{upstream_path}/{path}" if path else f"{upstream}{upstream_path}"
    body = await request.body()
    started = time.perf_counter()
    attempts = request.app.state.settings.upstream_max_retries if _is_retryable(request.method, headers) else 0
    try:
        for attempt in range(attempts + 1):
            upstream_response = await request.app.state.http.request(
                request.method, url, params=request.query_params, content=body, headers=headers
            )
            if upstream_response.status_code not in {502, 503, 504} or attempt == attempts:
                break
            UPSTREAM_RETRIES.labels(service).inc()
            await asyncio.sleep(0.05 * (2 ** attempt))
    except httpx.TimeoutException as exc:
        breaker.failure(service)
        UPSTREAM_REQUESTS.labels(service, "timeout").inc()
        raise GatewayError(504, "UPSTREAM_TIMEOUT", f"{service} service timed out") from exc
    except httpx.HTTPError as exc:
        breaker.failure(service)
        UPSTREAM_REQUESTS.labels(service, "unavailable").inc()
        raise GatewayError(502, "UPSTREAM_UNAVAILABLE", f"{service} service could not be reached") from exc
    UPSTREAM_LATENCY.labels(service).observe(time.perf_counter() - started)
    UPSTREAM_REQUESTS.labels(service, str(upstream_response.status_code)).inc()
    if upstream_response.status_code >= 500:
        breaker.failure(service)
    else:
        breaker.success(service)
    response_headers = {key: value for key, value in upstream_response.headers.items() if key.lower() not in HOP_BY_HOP}
    return Response(upstream_response.content, upstream_response.status_code, response_headers,
                    media_type=upstream_response.headers.get("content-type"))


async def proxy(service: str, request: Request, path: str = "") -> Response:
    if service not in SERVICE_PREFIXES:
        raise GatewayError(404, "SERVICE_NOT_FOUND", "The requested API service does not exist")
    principal = getattr(request.state, "principal", None)
    is_public_auth = (request.method, request.url.path) in {
        ("POST", "/api/v1/auth/register"),
        ("POST", "/api/v1/auth/login"), ("POST", "/api/v1/auth/refresh"),
        ("POST", "/api/v1/auth/forgot-password"),
        ("POST", "/api/v1/auth/password/reset/request"), ("POST", "/api/v1/auth/password/reset/confirm"),
    }
    if not is_public_auth:
        scope = _required_scope(service, request.method)
        if not principal or (scope not in principal.scopes and "gateway:admin" not in principal.scopes):
            raise GatewayError(403, "FORBIDDEN", "The authenticated principal lacks the required permission")
    return await forward(service, path, request)


for _method in ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
    router.add_api_route("/{service}", proxy, methods=[_method], operation_id=f"proxy_{_method.lower()}_service")
    router.add_api_route("/{service}/{path:path}", proxy, methods=[_method], operation_id=f"proxy_{_method.lower()}_service_path")
