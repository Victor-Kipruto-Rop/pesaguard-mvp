"""Redis-backed replay protection for payment-creation requests."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.cache import RedisCache


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST" or not request.url.path.startswith("/api/v1/payments"):
            return await call_next(request)

        token = request.headers.get("idempotency-key")
        if not token or len(token.strip()) > 255:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "IDEMPOTENCY_KEY_REQUIRED", "message": "A valid Idempotency-Key is required"}},
            )

        redis_cache: RedisCache | None = getattr(request.app.state, "redis_cache", None)
        redis = getattr(request.app.state, "redis", None)
        settings = getattr(getattr(request.app, "state", None), "settings", None)
        if not redis_cache and not redis or settings is None:
            return JSONResponse(
                status_code=503,
                content={"error": {"code": "IDEMPOTENCY_UNAVAILABLE", "message": "Payment processing is temporarily unavailable"}},
            )

        request_body = await request.body()
        body_hash = hashlib.sha256(request_body).hexdigest()
        subject = getattr(getattr(request.state, "principal", None), "subject", "anonymous")
        key = "idempotency:" + hashlib.sha256(f"{subject}:{request.url.path}:{token.strip()}".encode()).hexdigest()

        try:
            cached = await (redis_cache.get_json(key) if redis_cache else self._get_json(redis, key))
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"error": {"code": "IDEMPOTENCY_UNAVAILABLE", "message": "Payment processing is temporarily unavailable"}},
            )

        if cached:
            if cached.get("body_hash") != body_hash:
                return JSONResponse(
                    status_code=422,
                    content={"error": {"code": "IDEMPOTENCY_KEY_REUSED", "message": "Idempotency-Key cannot be reused with a different request"}},
                )
            return Response(
                cached.get("body", "").encode("utf-8"),
                status_code=cached.get("status", 200),
                headers={**cached.get("headers", {}), "Idempotency-Replayed": "true"},
            )

        lock_key = f"{key}:lock"
        release_lock = False
        try:
            acquired = await (
                redis_cache.set_if_not_exists(lock_key, "1", settings.idempotency_lock_seconds)
                if redis_cache
                else redis.set(lock_key, "1", nx=True, ex=settings.idempotency_lock_seconds)
            )
            if not acquired:
                return JSONResponse(
                    status_code=409,
                    content={"error": {"code": "IDEMPOTENCY_IN_PROGRESS", "message": "An identical payment request is in progress"}},
                    headers={"Retry-After": "2"},
                )

            response = await call_next(request)
            if response.status_code >= 500:
                release_lock = True
                return response

            body = b"".join([chunk async for chunk in response.body_iterator])
            headers = {
                name: value
                for name, value in response.headers.items()
                if name.lower() in {"content-type", "location", "cache-control", "etag", "x-request-id", "x-correlation-id"}
            }
            payload = {"status": response.status_code, "headers": headers, "body": body.decode(errors="replace"), "body_hash": body_hash}
            if redis_cache:
                await redis_cache.set_json(key, payload, settings.idempotency_ttl_seconds)
            else:
                await redis.set(key, json.dumps(payload), ex=settings.idempotency_ttl_seconds)
            release_lock = True
            return Response(body, status_code=response.status_code, headers=headers)
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"error": {"code": "IDEMPOTENCY_UNAVAILABLE", "message": "Payment processing is temporarily unavailable"}},
            )
        finally:
            if release_lock:
                try:
                    if redis_cache:
                        await redis_cache.delete(lock_key)
                    else:
                        await redis.delete(lock_key)
                except Exception:
                    pass

    @staticmethod
    async def _get_json(redis: Any, key: str) -> dict[str, Any] | None:
        value = await redis.get(key)
        if not value:
            return None
        return json.loads(value)
