"""Redis sliding-window rate limiting with per-identity policies and bounded local fallback."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.constants import PROBE_PATHS
from app.core.client_ip import client_ip
from app.metrics import RATE_LIMIT_DECISIONS
from app.responses import error_response


SLIDING_WINDOW_SCRIPT = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, tonumber(ARGV[2]) - tonumber(ARGV[3]))
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[1]) then return {0, 0} end
redis.call('ZADD', KEYS[1], ARGV[2], ARGV[4])
redis.call('PEXPIRE', KEYS[1], tonumber(ARGV[3]))
return {1, tonumber(ARGV[1]) - count - 1}
"""


RATE_LIMIT_HEADERS = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Policy", "X-RateLimit-Reset"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce an atomic sliding window for IP, user, or API-key derived identities."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        if self._should_skip(request):
            return await call_next(request)

        settings = getattr(getattr(request.app, "state", None), "settings", None)
        if settings is None:
            return await call_next(request)

        identity = self._identity(request)
        limit = self._limit(settings)
        try:
            allowed, remaining, backend = await self._consume(request, f"ratelimit:{identity}")
        except RateLimitUnavailable:
            payload = error_response("RATE_LIMIT_UNAVAILABLE", "Rate limiting is temporarily unavailable")
            return JSONResponse(status_code=503, content=payload.model_dump())

        if not allowed:
            RATE_LIMIT_DECISIONS.labels("denied", backend).inc()
            retry_after = self._retry_after_seconds(settings)
            payload = error_response("RATE_LIMITED", "Too many requests")
            return JSONResponse(
                status_code=429,
                content=payload.model_dump(),
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Policy": "sliding-window",
                },
            )

        RATE_LIMIT_DECISIONS.labels("allowed", backend).inc()
        response = await call_next(request)
        for name, value in self._rate_limit_headers(limit, remaining, settings).items():
            response.headers.setdefault(name, value)
        return response

    async def _consume(self, request: Request, key: str) -> tuple[bool, int, str]:
        settings = request.app.state.settings
        limit = self._limit(settings)
        now_ms = int(time.time() * 1000)
        redis = getattr(request.app.state, "redis", None)
        redis_cache = getattr(request.app.state, "redis_cache", None)
        logger = getattr(request.app.state, "logger", None)

        if redis_cache is not None:
            return await self._eval_redis(redis_cache, key, limit, now_ms, settings, logger)
        if redis is not None:
            return await self._eval_redis(redis, key, limit, now_ms, settings, logger)
        return (*self._consume_local(key, limit, settings.rate_limit_window_seconds), "local")

    async def _eval_redis(self, backend: Any, key: str, limit: int, now_ms: int, settings: Any, logger: Any) -> tuple[bool, int, str]:
        try:
            result = await backend.eval(
                SLIDING_WINDOW_SCRIPT,
                1,
                key,
                limit,
                now_ms,
                settings.rate_limit_window_seconds * 1000,
                f"{now_ms}:{uuid4()}",
            )
            return bool(int(result[0])), int(result[1]), "redis"
        except Exception:
            if logger:
                logger.warning("rate_limit_redis_unavailable")
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
    def _should_skip(request: Request) -> bool:
        return request.method in {"OPTIONS", "HEAD"} or request.url.path in PROBE_PATHS

    @staticmethod
    def _identity(request: Request) -> str:
        principal = getattr(request.state, "principal", None)
        if getattr(principal, "subject", None):
            return str(principal.subject)
        if request.headers.get("x-api-key"):
            return f"apikey:{request.headers.get('x-api-key')}"
        return getattr(request.state, "client_ip", None) or client_ip(request)

    @staticmethod
    def _limit(settings: Any) -> int:
        return settings.rate_limit_requests + settings.rate_limit_burst

    @staticmethod
    def _retry_after_seconds(settings: Any) -> int:
        return max(1, settings.rate_limit_window_seconds // max(1, settings.rate_limit_requests))

    @staticmethod
    def _rate_limit_headers(limit: int, remaining: int, settings: Any) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Policy": "sliding-window",
            "X-RateLimit-Reset": str(int(time.time()) + settings.rate_limit_window_seconds),
        }


class RateLimitUnavailable(Exception):
    """Internal fail-closed signal for an unavailable distributed limiter."""
