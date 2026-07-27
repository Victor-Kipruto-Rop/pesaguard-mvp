"""Redis-backed replay protection for payment-creation requests."""
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
        if not token or len(token) > 255:
            return JSONResponse(status_code=400, content={"error": {"code": "IDEMPOTENCY_KEY_REQUIRED", "message": "A valid Idempotency-Key is required"}})
        redis_cache: RedisCache | None = getattr(request.app.state, "redis_cache", None)
        redis = request.app.state.redis
        if not redis_cache and not redis:
            return JSONResponse(status_code=503, content={"error": {"code": "IDEMPOTENCY_UNAVAILABLE", "message": "Payment processing is temporarily unavailable"}})
        subject = getattr(getattr(request.state, "principal", None), "subject", "anonymous")
        key = "idempotency:" + hashlib.sha256(f"{subject}:{request.url.path}:{token}".encode()).hexdigest()
        body_hash = hashlib.sha256(await request.body()).hexdigest()
        try:
            cached = await (redis_cache.get_json(key) if redis_cache else self._get_json(redis, key))
        except Exception:
            return JSONResponse(status_code=503, content={"error": {"code": "IDEMPOTENCY_UNAVAILABLE", "message": "Payment processing is temporarily unavailable"}})
        if cached:
            if cached["body_hash"] != body_hash:
                return JSONResponse(status_code=422, content={"error": {"code": "IDEMPOTENCY_KEY_REUSED", "message": "Idempotency-Key cannot be reused with a different request"}})
            return Response(cached["body"].encode(), status_code=cached["status"], headers={**cached["headers"], "Idempotency-Replayed": "true"})
        lock_key = f"{key}:lock"
        release_lock = False
        try:
            if not await (redis_cache.set_if_not_exists(lock_key, "1", request.app.state.settings.idempotency_lock_seconds) if redis_cache else redis.set(lock_key, "1", nx=True, ex=request.app.state.settings.idempotency_lock_seconds)):
                return JSONResponse(status_code=409, content={"error": {"code": "IDEMPOTENCY_IN_PROGRESS", "message": "An identical payment request is in progress"}}, headers={"Retry-After": "2"})
            response = await call_next(request)
            if response.status_code >= 500:
                release_lock = True
                return response
            body = b"".join([chunk async for chunk in response.body_iterator])
            headers = {name: value for name, value in response.headers.items() if name.lower() in {"content-type", "location"}}
            if redis_cache:
                await redis_cache.set_json(key, {"status": response.status_code, "headers": headers, "body": body.decode(errors="replace"), "body_hash": body_hash}, request.app.state.settings.idempotency_ttl_seconds)
            else:
                await redis.set(key, json.dumps({"status": response.status_code, "headers": headers, "body": body.decode(errors="replace"), "body_hash": body_hash}), ex=request.app.state.settings.idempotency_ttl_seconds)
            release_lock = True
            return Response(body, status_code=response.status_code, headers=headers)
        except Exception:
            return JSONResponse(status_code=503, content={"error": {"code": "IDEMPOTENCY_UNAVAILABLE", "message": "Payment processing is temporarily unavailable"}})
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
