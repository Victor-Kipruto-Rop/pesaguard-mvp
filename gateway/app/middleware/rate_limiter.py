"""Redis sliding-window rate limiting with per-identity policies and bounded local fallback."""
import time
from collections import defaultdict, deque
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.client_ip import client_ip
from app.metrics import RATE_LIMIT_DECISIONS


SLIDING_WINDOW_SCRIPT = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, tonumber(ARGV[2]) - tonumber(ARGV[3]))
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[1]) then return {0, 0} end
redis.call('ZADD', KEYS[1], ARGV[2], ARGV[4])
redis.call('PEXPIRE', KEYS[1], tonumber(ARGV[3]))
return {1, tonumber(ARGV[1]) - count - 1}
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce an atomic sliding window for IP, user, or API-key derived identities."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in {"/health", "/ready", "/live", "/metrics"}:
            return await call_next(request)
        settings = request.app.state.settings
        identity = getattr(getattr(request.state, "principal", None), "subject", None) or client_ip(request)
        try:
            allowed, remaining, backend = await self._consume(request, f"ratelimit:{identity}")
        except RateLimitUnavailable:
            return JSONResponse(status_code=503, content={"error": {"code": "RATE_LIMIT_UNAVAILABLE", "message": "Rate limiting is temporarily unavailable"}})
        if not allowed:
            RATE_LIMIT_DECISIONS.labels("denied", backend).inc()
            retry_after = max(1, settings.rate_limit_window_seconds // max(1, settings.rate_limit_requests))
            return JSONResponse(status_code=429, content={"error": {"code": "RATE_LIMITED", "message": "Too many requests"}},
                                headers={"Retry-After": str(retry_after), "X-RateLimit-Limit": str(self._limit(settings)), "X-RateLimit-Remaining": "0"})
        RATE_LIMIT_DECISIONS.labels("allowed", backend).inc()
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limit(settings))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    async def _consume(self, request: Request, key: str) -> tuple[bool, int, str]:
        settings = request.app.state.settings
        limit = self._limit(settings)
        now_ms = int(time.time() * 1000)
        redis = request.app.state.redis
        redis_cache = getattr(request.app.state, "redis_cache", None)
        if redis_cache:
            try:
                result = await redis_cache.eval(SLIDING_WINDOW_SCRIPT, 1, key, limit, now_ms, settings.rate_limit_window_seconds * 1000,
                                               f"{now_ms}:{uuid4()}")
                return bool(int(result[0])), int(result[1]), "redis"
            except Exception:
                request.app.state.logger.warning("rate_limit_redis_unavailable")
                if settings.environment == "production" and not settings.rate_limit_fail_open:
                    RATE_LIMIT_DECISIONS.labels("unavailable", "redis").inc()
                    raise RateLimitUnavailable
        elif redis:
            try:
                result = await redis.eval(SLIDING_WINDOW_SCRIPT, 1, key, limit, now_ms, settings.rate_limit_window_seconds * 1000,
                                          f"{now_ms}:{uuid4()}")
                return bool(int(result[0])), int(result[1]), "redis"
            except Exception:
                request.app.state.logger.warning("rate_limit_redis_unavailable")
                if settings.environment == "production" and not settings.rate_limit_fail_open:
                    RATE_LIMIT_DECISIONS.labels("unavailable", "redis").inc()
                    raise RateLimitUnavailable
        return (*self._consume_local(key, limit, settings.rate_limit_window_seconds), "local")

    def _consume_local(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        window = self._windows[key]
        while window and window[0] <= now - window_seconds:
            window.popleft()
        if len(window) >= limit:
            return False, 0
        window.append(now)
        return True, limit - len(window)

    @staticmethod
    def _limit(settings) -> int:
        return settings.rate_limit_requests + settings.rate_limit_burst


class RateLimitUnavailable(Exception):
    """Internal fail-closed signal for an unavailable distributed limiter."""
