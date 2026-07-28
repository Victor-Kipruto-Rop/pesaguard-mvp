"""Service routing layer. Routes preserve method, body and approved request context."""
import asyncio
import time

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.clients.service_client import ServiceClientConnectionError, ServiceClientTimeout

from app.exceptions.handlers import GatewayError
from app.metrics import UPSTREAM_LATENCY, UPSTREAM_REQUESTS, UPSTREAM_RETRIES

router = APIRouter(prefix="/api/v1", tags=["Gateway"])
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "host"}
SENSITIVE_HEADERS = {"authorization", "x-api-key", "x-authenticated-subject", "x-authenticated-scopes"}
def _required_scope(service: str, method: str) -> str:
    action = "read" if method in {"GET", "HEAD", "OPTIONS"} else "write"
    return f"{service}:{action}"


def _is_retryable(method: str, headers: dict[str, str]) -> bool:
    return method in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"} or "idempotency-key" in headers


async def forward(service: str, path: str, request: Request) -> Response:
    settings = request.app.state.settings
    if not settings.route_config or service not in settings.route_services():
        raise GatewayError(404, "SERVICE_NOT_FOUND", "The requested API service does not exist")
    supported_methods = settings.supported_methods_for(service)
    if supported_methods and request.method not in supported_methods:
        raise GatewayError(405, "METHOD_NOT_ALLOWED", f"{service} service does not support {request.method}")
    upstream = settings.upstream_for(service)
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
    prefix = settings.path_prefix_for(service) or "/api/v1"
    upstream_path = f"{prefix}/{service}" if prefix == "/api/v1" else f"{prefix}"
    url = f"{upstream}{upstream_path}/{path}" if path else f"{upstream}{upstream_path}"
    body = await request.body()
    started = time.perf_counter()
    attempts = request.app.state.settings.upstream_max_retries if _is_retryable(request.method, headers) else 0
    try:
        for attempt in range(attempts + 1):
            upstream_response = await request.app.state.service_client.request(
                request.method,
                url,
                params=request.query_params,
                content=body,
                headers=headers,
                raise_for_status=False,
            )
            if upstream_response.status_code not in {502, 503, 504} or attempt == attempts:
                break
            UPSTREAM_RETRIES.labels(service).inc()
            await asyncio.sleep(0.05 * (2 ** attempt))
    except ServiceClientTimeout as exc:
        breaker.failure(service)
        UPSTREAM_REQUESTS.labels(service, "timeout").inc()
        raise GatewayError(504, "UPSTREAM_TIMEOUT", f"{service} service timed out") from exc
    except ServiceClientConnectionError as exc:
        breaker.failure(service)
        UPSTREAM_REQUESTS.labels(service, "unavailable").inc()
        raise GatewayError(502, "UPSTREAM_UNAVAILABLE", f"{service} service could not be reached") from exc
    except Exception as exc:
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
    if not request.app.state.settings.route_config or service not in request.app.state.settings.route_services():
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


def register_proxy_routes(router: APIRouter, settings) -> None:
    for service in settings.route_services():
        for _method in ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
            router.add_api_route(
                f"/{service}",
                proxy,
                methods=[_method],
                operation_id=f"proxy_{_method.lower()}_{service}",
            )
            router.add_api_route(
                f"/{service}/{{path:path}}",
                proxy,
                methods=[_method],
                operation_id=f"proxy_{_method.lower()}_{service}_path",
            )
