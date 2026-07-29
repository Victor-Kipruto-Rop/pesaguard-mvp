import hashlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from starlette.responses import Response

from app.config.settings import Settings
from app.middleware.idempotency import IdempotencyMiddleware
from app.responses import error_response


class DummyRequest(SimpleNamespace):
    pass


@pytest.mark.asyncio
async def test_idempotency_key_required_for_payment_posts():
    request = DummyRequest(method="POST", url=SimpleNamespace(path="/api/v1/payments"), headers={}, state=SimpleNamespace(), app=SimpleNamespace(state=SimpleNamespace(settings=Settings(environment="test"))))
    middleware = IdempotencyMiddleware(lambda scope, receive, send: Response("ok"))

    response = await middleware.dispatch(request, lambda req: Response("ok", status_code=200))

    assert response.status_code == 400
    payload = json.loads(response.body.decode())
    assert payload["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_idempotency_replays_cached_response_when_exact_body_matches():
    settings = Settings(environment="test")
    request = DummyRequest(
        method="POST",
        url=SimpleNamespace(path="/api/v1/payments"),
        headers={"idempotency-key": "abc123"},
        state=SimpleNamespace(principal=SimpleNamespace(subject="user-1")),
        app=SimpleNamespace(state=SimpleNamespace(settings=settings, redis=AsyncMock())),
    )
    body = b"{\"amount\":100}"
    request.body = AsyncMock(return_value=body)
    cached_payload = {"status": 200, "headers": {"content-type": "application/json"}, "body": body.decode(), "body_hash": hashlib.sha256(body).hexdigest()}
    request.app.state.redis.get.return_value = json.dumps(cached_payload)

    middleware = IdempotencyMiddleware(lambda scope, receive, send: Response("ok", status_code=200))
    response = await middleware.dispatch(request, lambda req: Response("ok", status_code=200))

    assert response.status_code == 200
    assert response.headers["Idempotency-Replayed"] == "true"


@pytest.mark.asyncio
async def test_idempotency_rejects_key_reuse_with_different_body():
    settings = Settings(environment="test")
    request = DummyRequest(
        method="POST",
        url=SimpleNamespace(path="/api/v1/payments"),
        headers={"idempotency-key": "abc123"},
        state=SimpleNamespace(principal=SimpleNamespace(subject="user-1")),
        app=SimpleNamespace(state=SimpleNamespace(settings=settings, redis=AsyncMock())),
    )
    body = b"{\"amount\":100}"
    request.body = AsyncMock(return_value=body)
    cached_payload = {"status": 200, "headers": {"content-type": "application/json"}, "body": "{}", "body_hash": hashlib.sha256(b"{}" ).hexdigest()}
    request.app.state.redis.get.return_value = json.dumps(cached_payload)

    middleware = IdempotencyMiddleware(lambda scope, receive, send: Response("ok", status_code=200))
    response = await middleware.dispatch(request, lambda req: Response("ok", status_code=200))

    assert response.status_code == 422
    payload = json.loads(response.body.decode())
    assert payload["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


@pytest.mark.asyncio
async def test_idempotency_stores_response_after_successful_request():
    settings = Settings(environment="test")
    redis = AsyncMock()
    request = DummyRequest(
        method="POST",
        url=SimpleNamespace(path="/api/v1/payments"),
        headers={"idempotency-key": "abc123"},
        state=SimpleNamespace(principal=SimpleNamespace(subject="user-1")),
        app=SimpleNamespace(state=SimpleNamespace(settings=settings, redis=redis)),
    )
    body = b"{\"amount\":100}"
    request.body = AsyncMock(return_value=body)
    request.app.state.redis.get.return_value = None
    request.app.state.redis.get.return_value = None

    async def call_next(req):
        return Response(body, status_code=201, headers={"content-type": "application/json"})

    middleware = IdempotencyMiddleware(lambda scope, receive, send: None)
    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 201
    assert redis.set.await_count >= 1
