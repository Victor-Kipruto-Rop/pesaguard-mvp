"""Redis-backed replay protection for payment-creation requests."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.cache import RedisCache
from app.responses import error_response


IDEMPOTENCY_KEY_HEADER = "idempotency-key"
ALLOWED_RESPONSE_HEADERS = {
    "content-type",
    "location",
    "cache-control",
    "etag",
    "x-request-id",
    "x-correlation-id",
}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST" or not request.url.path.startswith("/api/v1/payments"):
            return await call_next(request)

        token = request.headers.get(IDEMPOTENCY_KEY_HEADER, "").strip()
        if not token or len(token) > 255:
            payload = error_response("IDEMPOTENCY_KEY_REQUIRED", "A valid Idempotency-Key is required")
            return JSONResponse(status_code=400, content=payload.model_dump())

        settings = getattr(getattr(request.app, "state", None), "settings", None)
        if settings is None:
            payload = error_response("IDEMPOTENCY_UNAVAILABLE", "Payment processing is temporarily unavailable")
            return JSONResponse(status_code=503, content=payload.model_dump())

        redis_cache: RedisCache | None = getattr(request.app.state, "redis_cache", None)
        redis = getattr(request.app.state, "redis", None)
        if redis_cache is None and redis is None:
            payload = error_response("IDEMPOTENCY_UNAVAILABLE", "Payment processing is temporarily unavailable")
            return JSONResponse(status_code=503, content=payload.model_dump())

        request_body = await request.body()
        body_hash = hashlib.sha256(request_body).hexdigest()
        subject = getattr(getattr(request.state, "principal", None), "subject", "anonymous")
        key = self._storage_key(subject, request.url.path, token)

        try:
            cached = await self._load_cache(redis_cache, redis, key)
        except Exception:
            payload = error_response("IDEMPOTENCY_UNAVAILABLE", "Payment processing is temporarily unavailable")
            return JSONResponse(status_code=503, content=payload.model_dump())

        if cached:
            if cached.get("body_hash") != body_hash:
                payload = error_response(
                    "IDEMPOTENCY_KEY_REUSED",
                    "Idempotency-Key cannot be reused with a different request",
                )
                return JSONResponse(status_code=422, content=payload.model_dump())
            response = Response(
                cached.get("body", "").encode("utf-8"),
                status_code=cached.get("status", 200),
                headers={**cached.get("headers", {}), "Idempotency-Replayed": "true"},
            )
            return response

        lock_key = f"{key}:lock"
        acquired = False
        try:
            acquired = await self._acquire_lock(redis_cache, redis, lock_key, settings.idempotency_lock_seconds)
            if not acquired:
                payload = error_response("IDEMPOTENCY_IN_PROGRESS", "An identical payment request is in progress")
                return JSONResponse(status_code=409, content=payload.model_dump(), headers={"Retry-After": "2"})

            response = await call_next(request)
            if response.status_code >= 500:
                return response

            body = response.body if getattr(response, "body", None) is not None else b"".join(
                [chunk async for chunk in response.body_iterator]
            )
            response_headers = self._serialize_response_headers(response.headers or {})
            payload = {
                "status": response.status_code,
                "headers": response_headers,
                "body": body.decode(errors="replace"),
                "body_hash": body_hash,
            }
            await self._store_cache(redis_cache, redis, key, payload, settings.idempotency_ttl_seconds)
            return Response(body, status_code=response.status_code, headers=response_headers)
        except Exception:
            payload = error_response("IDEMPOTENCY_UNAVAILABLE", "Payment processing is temporarily unavailable")
            return JSONResponse(status_code=503, content=payload.model_dump())
        finally:
            if acquired:
                await self._release_lock(redis_cache, redis, lock_key)

    @staticmethod
    def _storage_key(subject: str, path: str, token: str) -> str:
        digest = hashlib.sha256(f"{subject}:{path}:{token}".encode()).hexdigest()
        return f"idempotency:{digest}"

    @staticmethod
    async def _load_cache(redis_cache: RedisCache | None, redis: Any | None, key: str) -> dict[str, Any] | None:
        if redis_cache is not None:
            return await redis_cache.get_json(key)
        return await IdempotencyMiddleware._get_json(redis, key)

    @staticmethod
    async def _store_cache(redis_cache: RedisCache | None, redis: Any | None, key: str, payload: dict[str, Any], ttl: int) -> None:
        if redis_cache is not None:
            await redis_cache.set_json(key, payload, ttl)
        else:
            await redis.set(key, json.dumps(payload), ex=ttl)

    @staticmethod
    async def _acquire_lock(redis_cache: RedisCache | None, redis: Any | None, key: str, ttl: int) -> bool:
        if redis_cache is not None:
            return await redis_cache.set_if_not_exists(key, "1", ttl)
        return bool(await redis.set(key, "1", nx=True, ex=ttl))

    @staticmethod
    async def _release_lock(redis_cache: RedisCache | None, redis: Any | None, key: str) -> None:
        try:
            if redis_cache is not None:
                await redis_cache.delete(key)
            elif redis is not None:
                await redis.delete(key)
        except Exception:
            pass

    @staticmethod
    def _serialize_response_headers(headers: dict[str, str]) -> dict[str, str]:
        return {name: value for name, value in headers.items() if name.lower() in ALLOWED_RESPONSE_HEADERS}

    @staticmethod
    async def _get_json(redis: Any, key: str) -> dict[str, Any] | None:
        value = await redis.get(key)
        if not value:
            return None
        return json.loads(value)
