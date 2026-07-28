"""Request IDs, correlation propagation, structured logs, timing, and metrics."""
from __future__ import annotations

import time
from typing import Awaitable, Callable
from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.metrics import LATENCY, REQUESTS


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = self._header(request, "x-request-id") or str(uuid4())
        correlation_id = self._header(request, "x-correlation-id") or self._header(request, "x-trace-id") or request_id
        trace_id = self._header(request, "traceparent") or correlation_id

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request.state.trace_id = trace_id
        request.state.client_ip = getattr(request.client, "host", "unknown") if request.client else "unknown"
        request.state.request_path = request.url.path
        request.state.request_method = request.method
        started_at = time.perf_counter()
        response: Response | None = None

        try:
            with structlog.contextvars.bound_contextvars(
                request_id=request_id,
                correlation_id=correlation_id,
                trace_id=trace_id,
                request_method=request.method,
                request_path=request.url.path,
                client_ip=request.state.client_ip,
            ):
                response = await call_next(request)
                return response
        finally:
            duration = time.perf_counter() - started_at
            route = request.scope.get("route")
            path = route.path if route else request.url.path
            status = response.status_code if response else 500
            REQUESTS.labels(request.method, path, status).inc()
            LATENCY.labels(request.method, path).observe(duration)
            structlog.get_logger("pesaguard.gateway").info(
                "request_complete",
                method=request.method,
                path=path,
                status_code=status,
                duration_ms=round(duration * 1000, 2),
                request_id=request_id,
                correlation_id=correlation_id,
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Correlation-ID"] = correlation_id
                response.headers["X-Trace-ID"] = trace_id

    @staticmethod
    def _header(request: Request, name: str) -> str | None:
        value = request.headers.get(name)
        return value.strip() if value and value.strip() else None
