from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from starlette.responses import Response

from app.config.settings import Settings
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security import SecurityMiddleware


class DummyRequest(SimpleNamespace):
    pass


@pytest.mark.asyncio
async def test_request_context_middleware_sets_ids_and_headers():
    middleware = RequestContextMiddleware(lambda scope, receive, send: None)
    request = DummyRequest(
        headers={},
        url=SimpleNamespace(path="/api/v1/health", scheme="http"),
        method="GET",
        scope={"route": None},
        state=SimpleNamespace(),
        client=SimpleNamespace(host="203.0.113.10"),
        app=SimpleNamespace(state=SimpleNamespace(settings=Settings(environment="test"))),
    )

    async def call_next(req):
        return Response("ok")

    response = await middleware.dispatch(request, call_next)

    assert request.state.request_id
    assert request.state.correlation_id == request.state.request_id
    assert response.headers["X-Request-ID"] == request.state.request_id
    assert response.headers["X-Correlation-ID"] == request.state.correlation_id


@pytest.mark.asyncio
async def test_security_middleware_sets_hardening_headers(monkeypatch):
    middleware = SecurityMiddleware(lambda scope, receive, send: None)
    settings = Settings(environment="test", allowed_ips=["127.0.0.1"], denied_ips=[], request_max_bytes=1024)
    request = DummyRequest(
        headers={},
        url=SimpleNamespace(path="/api/v1/test", scheme="https"),
        method="GET",
        scope={},
        state=SimpleNamespace(),
        client=SimpleNamespace(host="127.0.0.1"),
        app=SimpleNamespace(state=SimpleNamespace(settings=settings)),
        body=AsyncMock(return_value=b""),
    )

    async def call_next(req):
        return Response("ok")

    response = await middleware.dispatch(request, call_next)

    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.asyncio
async def test_authentication_middleware_sets_principal_for_bearer_tokens(monkeypatch):
    middleware = AuthenticationMiddleware(lambda scope, receive, send: None)
    settings = Settings(environment="test")
    request = DummyRequest(
        headers={"authorization": "Bearer demo-token"},
        url=SimpleNamespace(path="/api/v1/payments", scheme="https"),
        method="POST",
        scope={},
        state=SimpleNamespace(),
        client=SimpleNamespace(host="127.0.0.1"),
        app=SimpleNamespace(state=SimpleNamespace(settings=settings, service_client=None, jwks_cache=None)),
    )

    principal = SimpleNamespace(subject="user-123", auth_scheme="bearer")
    monkeypatch.setattr("app.middleware.authentication.verify_token", AsyncMock(return_value=principal))
    monkeypatch.setattr("app.middleware.authentication.emit", lambda *args, **kwargs: None)

    async def call_next(req):
        return Response("ok")

    response = await middleware.dispatch(request, call_next)

    assert request.state.principal is principal
    assert request.state.auth_context["scheme"] == "bearer"
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_authentication_middleware_accepts_apikey_authorization_scheme(monkeypatch):
    middleware = AuthenticationMiddleware(lambda scope, receive, send: None)
    settings = Settings(environment="test")
    request = DummyRequest(
        headers={"authorization": "ApiKey demo-key"},
        url=SimpleNamespace(path="/api/v1/payments", scheme="https"),
        method="POST",
        scope={},
        state=SimpleNamespace(),
        client=SimpleNamespace(host="127.0.0.1"),
        app=SimpleNamespace(state=SimpleNamespace(settings=settings, service_client=None, jwks_cache=None)),
    )

    principal = SimpleNamespace(subject="api-key:demo", auth_scheme="api_key")
    monkeypatch.setattr("app.middleware.authentication.verify_api_key", lambda api_key, settings: principal)
    monkeypatch.setattr("app.middleware.authentication.emit", lambda *args, **kwargs: None)

    async def call_next(req):
        return Response("ok")

    response = await middleware.dispatch(request, call_next)

    assert request.state.principal is principal
    assert request.state.auth_context["scheme"] == "api_key"
    assert response.status_code == 200
