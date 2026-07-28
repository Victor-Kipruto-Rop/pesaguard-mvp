"""Service routing layer. Routes preserve method, body and approved request context."""
from __future__ import annotations

import asyncio
import time
from functools import partial
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.clients.service_client import ServiceClientConnectionError, ServiceClientTimeout
from app.constants import (
    AUTHENTICATED_SCOPES_HEADER,
    AUTHENTICATED_SUBJECT_HEADER,
    AUTH_PUBLIC_ROUTES,
    CORRELATION_ID_HEADER,
    DEFAULT_API_PREFIX,
    HOP_BY_HOP_HEADERS,
    REQUEST_ID_HEADER,
    SENSITIVE_HEADERS,
)
from app.exceptions.handlers import GatewayError
from app.metrics import UPSTREAM_LATENCY, UPSTREAM_REQUESTS, UPSTREAM_RETRIES

router = APIRouter(prefix=DEFAULT_API_PREFIX, tags=["Gateway"])


def _required_scope(service: str, method: str) -> str:
    action = "read" if method in {"GET", "HEAD", "OPTIONS"} else "write"
    return f"{service}:{action}"


def _is_retryable(method: str, headers: dict[str, str]) -> bool:
    return method in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"} or "idempotency-key" in headers


def _build_upstream_url(service: str, path: str, settings: Any, upstream: str) -> str:
    prefix = settings.path_prefix_for(service) or f"/{service}"
    if "{service}" in prefix:
        upstream_path = prefix.format(service=service)
    else:
        upstream_path = f"{prefix.rstrip('/')}/{service}" if prefix != "/" else f"/{service}"
    if path:
        normalized_path = path.lstrip("/")
        return f"{upstream.rstrip('/')}{upstream_path.rstrip('/')}/{normalized_path}"
    return f"{upstream.rstrip('/')}{upstream_path.rstrip('/')}"


def _gateway_route_path(service: str, settings: Any) -> str:
    route_path = settings.gateway_path_for(service) or f"/{service}"
    if route_path == "/":
        return "/"
    return route_path.rstrip("/") or "/"


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

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS | SENSITIVE_HEADERS
    }
    headers.update({REQUEST_ID_HEADER: getattr(request.state, "request_id", ""), CORRELATION_ID_HEADER: getattr(request.state, "correlation_id", "")})
    principal = getattr(request.state, "principal", None)
    if principal:
        headers[AUTHENTICATED_SUBJECT_HEADER] = principal.subject
        headers[AUTHENTICATED_SCOPES_HEADER] = " ".join(sorted(principal.scopes))

    body = await request.body()
    started = time.perf_counter()
    attempts = settings.upstream_max_retries if _is_retryable(request.method, headers) else 0
    upstream_response = None
    try:
        for attempt in range(attempts + 1):
            upstream_response = await request.app.state.service_client.request(
                request.method,
                _build_upstream_url(service, path, settings, upstream),
                params=request.query_params,
                content=body,
                headers=headers,
                raise_for_status=False,
                trace_id=getattr(request.state, "trace_id", None),
            )
            if upstream_response.status_code not in {502, 503, 504} or attempt == attempts:
                break
            UPSTREAM_RETRIES.labels(service).inc()
            await asyncio.sleep(0.05 * (2**attempt))
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
    if upstream_response is None:
        raise GatewayError(502, "UPSTREAM_UNAVAILABLE", f"{service} service could not be reached")
    UPSTREAM_REQUESTS.labels(service, str(upstream_response.status_code)).inc()
    if upstream_response.status_code >= 500:
        breaker.failure(service)
    else:
        breaker.success(service)

    response_headers = {
        key: value for key, value in upstream_response.headers.items() if key.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        upstream_response.content,
        upstream_response.status_code,
        response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )


async def proxy(service: str, request: Request, path: str = "") -> Response:
    if not request.app.state.settings.route_config or service not in request.app.state.settings.route_services():
        raise GatewayError(404, "SERVICE_NOT_FOUND", "The requested API service does not exist")
    principal = getattr(request.state, "principal", None)
    is_public_auth = (request.method, request.url.path) in AUTH_PUBLIC_ROUTES
    if not is_public_auth:
        scope = _required_scope(service, request.method)
        if not principal or (scope not in principal.scopes and "gateway:admin" not in principal.scopes):
            raise GatewayError(403, "FORBIDDEN", "The authenticated principal lacks the required permission")
    return await forward(service, path, request)


def _proxy_handler(service: str):
    async def handler(request: Request, path: str = "") -> Response:
        return await proxy(service, request, path)

    handler.__name__ = f"proxy_{service}"
    return handler


def register_proxy_routes(router: APIRouter, settings) -> None:
    if not settings.route_config:
        return
    for service in settings.route_services():
        methods = list(settings.supported_methods_for(service) or [])
        if "OPTIONS" not in methods:
            methods.append("OPTIONS")
        proxy_with_service = _proxy_handler(service)
        route_path = _gateway_route_path(service, settings)
        for _method in methods:
            router.add_api_route(
                route_path,
                proxy_with_service,
                methods=[_method],
                operation_id=f"proxy_{_method.lower()}_{service}",
            )
            router.add_api_route(
                f"{route_path}/{{path:path}}",
                proxy_with_service,
                methods=[_method],
                operation_id=f"proxy_{_method.lower()}_{service}_path",
            )
