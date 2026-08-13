"""Service routing layer. Routes preserve method, body and approved request context."""
from __future__ import annotations

import asyncio
import time
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import Response
from websockets import connect as ws_connect

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
from app.services import RouteManager

router = APIRouter(prefix=DEFAULT_API_PREFIX, tags=["Gateway"])


def _required_scope(service: str, method: str) -> str:
    action = "read" if method in {"GET", "HEAD", "OPTIONS"} else "write"
    return f"{service}:{action}"


def _is_retryable(method: str, headers: dict[str, str]) -> bool:
    return method in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"} or "idempotency-key" in headers


async def forward(service: str, path: str, request: Request) -> Response:
    settings = request.app.state.settings
    route_manager = getattr(request.app.state, "route_manager", None)
    if route_manager is None:
        route_manager = RouteManager(settings)
        setattr(request.app.state, "route_manager", route_manager)
    if not route_manager.service_exists(service):
        raise GatewayError(404, "SERVICE_NOT_FOUND", "The requested API service does not exist")
    supported_methods = settings.supported_methods_for(service)
    if supported_methods and request.method not in supported_methods:
        raise GatewayError(405, "METHOD_NOT_ALLOWED", f"{service} service does not support {request.method}")
    # prefer a healthy upstream detected via the service client; fall back to configured upstream logic
    upstream = await route_manager.select_healthy_upstream(service, request.app.state.service_client)
    if not upstream:
        # fall back to legacy resolver
        upstream = route_manager.resolve_service_url(service)
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
                route_manager.build_upstream_url(service, path),
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


def _to_websocket_url(url: str) -> str:
    if url.startswith("ws://") or url.startswith("wss://"):
        return url
    if url.startswith("http://"):
        return f"ws://{url[len('http://'):]}"
    if url.startswith("https://"):
        return f"wss://{url[len('https://'):]}"
    raise ValueError("invalid upstream URL scheme for websocket proxy")


def _websocket_headers(websocket: WebSocket) -> tuple[dict[str, str], list[str]]:
    subprotocols: list[str] = []
    headers: dict[str, str] = {}
    for key, value in websocket.headers.items():
        normalized_key = key.lower()
        if normalized_key in HOP_BY_HOP_HEADERS | SENSITIVE_HEADERS:
            continue
        if normalized_key.startswith("sec-websocket-"):
            if normalized_key == "sec-websocket-protocol":
                subprotocols = [protocol.strip() for protocol in value.split(",") if protocol.strip()]
            continue
        headers[key] = value
    headers.update({REQUEST_ID_HEADER: getattr(websocket.state, "request_id", ""), CORRELATION_ID_HEADER: getattr(websocket.state, "correlation_id", "")})
    principal = getattr(websocket.state, "principal", None)
    if principal:
        headers[AUTHENTICATED_SUBJECT_HEADER] = principal.subject
        headers[AUTHENTICATED_SCOPES_HEADER] = " ".join(sorted(principal.scopes))
    return headers, subprotocols


async def _bridge_websocket(client_ws: WebSocket, upstream_ws: Any) -> None:
    async def _client_to_upstream() -> None:
        while True:
            message = await client_ws.receive()
            if message["type"] == "websocket.receive":
                if "text" in message:
                    await upstream_ws.send(message["text"])
                elif "bytes" in message:
                    await upstream_ws.send(message["bytes"])
            elif message["type"] == "websocket.disconnect":
                await upstream_ws.close()
                break

    async def _upstream_to_client() -> None:
        async for message in upstream_ws:
            if isinstance(message, str):
                await client_ws.send_text(message)
            else:
                await client_ws.send_bytes(message)

    client_task = asyncio.create_task(_client_to_upstream())
    upstream_task = asyncio.create_task(_upstream_to_client())
    done, pending = await asyncio.wait({client_task, upstream_task}, return_when=asyncio.FIRST_EXCEPTION)
    for task in pending:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
    for task in done:
        if task.exception():
            raise task.exception()


async def websocket_proxy(service: str, websocket: WebSocket, path: str = "") -> None:
    if not websocket.app.state.settings.route_config or service not in websocket.app.state.settings.route_services():
        await websocket.close(code=1001)
        return

    principal = getattr(websocket.state, "principal", None)
    scope = _required_scope(service, "GET")
    if not principal or (scope not in principal.scopes and "gateway:admin" not in principal.scopes):
        await websocket.close(code=1008)
        return

    route_manager = getattr(websocket.app.state, "route_manager", None)
    if route_manager is None:
        route_manager = RouteManager(websocket.app.state.settings)
        setattr(websocket.app.state, "route_manager", route_manager)

    # prefer a healthy upstream for websocket as well
    upstream = await route_manager.select_healthy_upstream(service, websocket.app.state.service_client)
    if not upstream:
        upstream = route_manager.resolve_service_url(service)
    if not upstream:
        await websocket.close(code=1011)
        return

    try:
        websocket_url = _to_websocket_url(route_manager.build_upstream_url(service, path))
    except ValueError:
        await websocket.close(code=1011)
        return

    headers, subprotocols = _websocket_headers(websocket)
    if websocket.scope.get("query_string"):
        query_string = websocket.scope["query_string"].decode("utf-8")
        if query_string:
            websocket_url = f"{websocket_url}?{query_string}"

    await websocket.accept()
    try:
        async with ws_connect(websocket_url, extra_headers=headers, subprotocols=subprotocols or None) as upstream_ws:
            await _bridge_websocket(websocket, upstream_ws)
    except Exception:
        await websocket.close(code=1011)


def _proxy_websocket_handler(service: str):
    async def handler(websocket: WebSocket, path: str = "") -> None:
        await websocket_proxy(service, websocket, path)

    handler.__name__ = f"proxy_websocket_{service}"
    return handler


def register_proxy_routes(router: APIRouter, settings) -> None:
    if not settings.route_config:
        return
    route_manager = RouteManager(settings)
    for service in settings.route_services():
        methods = list(settings.supported_methods_for(service) or [])
        if "OPTIONS" not in methods:
            methods.append("OPTIONS")
        proxy_with_service = _proxy_handler(service)
        route_path = route_manager.gateway_route(service)
        for _method in methods:
            router.add_api_route(
                route_path,
                proxy_with_service,
                methods=[_method],
            )
            router.add_api_route(
                f"{route_path}/{{path:path}}",
                proxy_with_service,
                methods=[_method],
            )

        if settings.supports_websocket_for(service):
            websocket_with_service = _proxy_websocket_handler(service)
            router.add_api_websocket_route(
                route_path,
                websocket_with_service,
                name=f"proxy_websocket_{service}",
            )
            router.add_api_websocket_route(
                f"{route_path}/{{path:path}}",
                websocket_with_service,
                name=f"proxy_websocket_{service}_path",
            )
