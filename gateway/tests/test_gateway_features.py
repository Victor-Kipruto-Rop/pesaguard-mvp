from pathlib import Path

from fastapi import APIRouter
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

from app.config.settings import Settings
from app.main import create_app
from app.middleware.response_transform import ResponseTransformMiddleware
from app.routes.proxy import register_proxy_routes
from app.services import RouteManager


def test_response_transform_middleware_applies_route_specific_cache_and_headers(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    gateway_path: /payments\n    cache_control: public, max-age=60\n    response_headers:\n      X-Gateway-Mode: proxy\n      X-Response-Transform: enabled\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    app = Starlette()
    app.state.settings = settings
    app.state.route_manager = RouteManager(settings)
    app.add_middleware(ResponseTransformMiddleware)

    @app.route("/payments")
    async def payments(request):
        return PlainTextResponse("ok")

    client = TestClient(app)
    response = client.get("/payments")

    assert response.headers["Cache-Control"] == "public, max-age=60"
    assert response.headers["X-Gateway-Mode"] == "proxy"
    assert response.headers["X-Response-Transform"] == "enabled"


def test_create_app_exposes_enriched_openapi_metadata(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  auth:\n    env_var: PESAGUARD_AUTH_SERVICE_URL\n    gateway_path: /identity/auth\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    app = create_app(settings)
    openapi = app.openapi()

    assert openapi["info"]["title"] == settings.app_name
    assert "gateway routing" in openapi["info"]["description"].lower()
    assert openapi["servers"] == [{"url": "/", "description": "Gateway"}]
    assert any(tag["name"] == "Gateway" for tag in openapi["tags"])


def test_websocket_routes_use_proxy_handler(tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  chat:\n    env_var: PESAGUARD_CHAT_SERVICE_URL\n    websocket: true\n",
        encoding="utf-8",
    )

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    router = APIRouter(prefix="/api/v1")
    register_proxy_routes(router, settings)

    websocket_routes = [route for route in router.routes if route.__class__.__name__ == "APIWebSocketRoute"]
    assert websocket_routes
    assert any(getattr(route, "endpoint").__name__ == "proxy_websocket_chat" for route in websocket_routes)
