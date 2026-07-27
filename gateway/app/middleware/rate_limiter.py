"""Redis-backed fixed-window limiter with safe in-memory local fallback."""
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._windows: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in {"/health", "/ready", "/live", "/metrics"}:
            return await call_next(request)
        settings = request.app.state.settings
        identity = getattr(getattr(request.state, "principal", None), "subject", None) or (request.client.host if request.client else "unknown")
        key, now = f"ratelimit:{identity}", int(time.time())
        redis = request.app.state.redis
        if redis:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, settings.rate_limit_window_seconds)
        else:
            start = now - (now % settings.rate_limit_window_seconds)
            count, window = self._windows[key]
            current = count + 1 if window == start else 1
            self._windows[key] = (current, start)
        remaining = max(0, settings.rate_limit_requests - current)
        if current > settings.rate_limit_requests:
            return JSONResponse(status_code=429, content={"error": {"code": "RATE_LIMITED", "message": "Too many requests"}},
                                headers={"Retry-After": str(settings.rate_limit_window_seconds)})
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
