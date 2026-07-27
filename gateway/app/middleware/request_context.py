"""Request IDs, correlation propagation, structured logs, timing, and metrics."""
import time
from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.metrics import LATENCY, REQUESTS


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        correlation_id = request.headers.get("x-correlation-id", request_id)
        request.state.request_id, request.state.correlation_id = request_id, correlation_id
        start = time.perf_counter()
        response: Response | None = None
        try:
            with structlog.contextvars.bound_contextvars(request_id=request_id, correlation_id=correlation_id):
                response = await call_next(request)
                return response
        finally:
            duration = time.perf_counter() - start
            path = request.scope.get("route").path if request.scope.get("route") else request.url.path
            status = response.status_code if response else 500
            REQUESTS.labels(request.method, path, status).inc()
            LATENCY.labels(request.method, path).observe(duration)
            structlog.get_logger("pesaguard.gateway").info("request_complete", method=request.method, path=path,
                                                            status_code=status, duration_ms=round(duration * 1000, 2))
            if response:
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Correlation-ID"] = correlation_id
