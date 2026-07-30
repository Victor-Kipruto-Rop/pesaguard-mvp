import pytest

from app.config.settings import Settings
from app.constants import DEFAULT_API_PREFIX
from app.services import GatewayServiceManager, RouteManager
from app.utils import is_health_probe, normalize_headers, strip_sensitive_headers


def test_route_manager_resolves_gateway_route_from_settings(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    gateway_path: /payments\n"
    )
    monkeypatch.delenv("PESAGUARD_PAYMENTS_SERVICE_URL", raising=False)
    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    assert route_manager.service_exists("payments")
    assert route_manager.gateway_route("payments") == "/payments"
    assert route_manager.resolve_service_url("payments") is None
    assert route_manager.service_names() == ("payments",)


def test_route_manager_build_upstream_url_with_default_prefix(monkeypatch, tmp_path):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    path_prefix: /internal/{service}\n"
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_SERVICE_URL", "https://payments.local")
    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    assert route_manager.build_upstream_url("payments", "charge") == "https://payments.local/internal/payments/charge"


def test_header_helpers_normalize_and_strip():
    headers = {"Authorization": "Bearer tok", "X-Custom": "value", "": "ignored"}
    normalized = normalize_headers(headers)
    assert normalized == {"authorization": "Bearer tok", "x-custom": "value"}
    stripped = strip_sensitive_headers(normalized, ["authorization"])
    assert stripped == {"x-custom": "value"}


def test_gateway_service_manager_builds_runtime_snapshot(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    env_var: PESAGUARD_PAYMENTS_SERVICE_URL\n    gateway_path: /payments\n    methods: [GET, POST]\n"
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_SERVICE_URL", "https://payments.internal")
    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path, redis_url="redis://localhost:6379/0")
    manager = GatewayServiceManager(settings)

    snapshot = manager.runtime_snapshot()

    assert snapshot["service"] == "gateway"
    assert snapshot["route_count"] == 1
    assert snapshot["configured_upstreams"] == ["payments"]
    assert snapshot["services"][0]["name"] == "payments"
    assert snapshot["services"][0]["configured"] is True


def test_health_probe_detector():
    assert is_health_probe("/metrics", {"/health", "/metrics"})
    assert not is_health_probe("/api/v1/payments", {"/health", "/metrics"})


def test_route_manager_weighted_round_robin(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    upstreams:\n      - env_var: PESAGUARD_PAYMENTS_A\n        weight: 1\n      - env_var: PESAGUARD_PAYMENTS_B\n        weight: 1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_A", "https://payments-a.example.com")
    monkeypatch.setenv("PESAGUARD_PAYMENTS_B", "https://payments-b.example.com")

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    selections = [route_manager.select_upstream_round_robin("payments") for _ in range(4)]
    assert len(set(selections)) == 2
    assert "https://payments-a.example.com" in selections
    assert "https://payments-b.example.com" in selections


def test_route_manager_weighted_round_robin_with_weights(tmp_path, monkeypatch):
    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    upstreams:\n      - env_var: PESAGUARD_PAYMENTS_A\n        weight: 1\n      - env_var: PESAGUARD_PAYMENTS_B\n        weight: 3\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_A", "https://payments-a.example.com")
    monkeypatch.setenv("PESAGUARD_PAYMENTS_B", "https://payments-b.example.com")

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    selections = [route_manager.select_upstream_round_robin("payments") for _ in range(40)]
    assert "https://payments-a.example.com" in selections
    assert "https://payments-b.example.com" in selections


def test_select_healthy_upstream_prefers_healthy_candidate(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import asyncio

    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  payments:\n    upstreams:\n      - env_var: PESAGUARD_PAYMENTS_A\n        weight: 1\n      - env_var: PESAGUARD_PAYMENTS_B\n        weight: 1\n    health_path: /health\n    health_method: GET\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PESAGUARD_PAYMENTS_A", "https://payments-a.example.com")
    monkeypatch.setenv("PESAGUARD_PAYMENTS_B", "https://payments-b.example.com")

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    async def fake_request(method, path, **kwargs):
        # mark payments-b as healthy only
        if path.startswith("https://payments-b.example.com"):
            return SimpleNamespace(status_code=200)
        return SimpleNamespace(status_code=502)

    service_client = SimpleNamespace(request=fake_request)

    selected = asyncio.run(route_manager.select_healthy_upstream("payments", service_client))
    assert selected == "https://payments-b.example.com"


def test_select_healthy_upstream_uses_fallback_when_none_healthy(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import asyncio

    config_path = tmp_path / "routes.yaml"
    config_path.write_text(
        "version: v1\nservices:\n  primary:\n    upstreams:\n      - env_var: PESAGUARD_PRIMARY_A\n        weight: 1\n    fallback: false\n  fallback:\n    upstreams:\n      - env_var: PESAGUARD_FALLBACK_A\n        weight: 1\n    fallback: true\n    health_path: /health\n    health_method: GET\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PESAGUARD_PRIMARY_A", "https://primary.example.com")
    monkeypatch.setenv("PESAGUARD_FALLBACK_A", "https://fallback.example.com")

    settings = Settings(environment="test", allowed_hosts=["testserver"], route_config_path=config_path)
    route_manager = RouteManager(settings)

    async def fake_request(method, path, **kwargs):
        # primary is unhealthy, fallback healthy
        if path.startswith("https://primary.example.com"):
            return SimpleNamespace(status_code=502)
        if path.startswith("https://fallback.example.com"):
            return SimpleNamespace(status_code=200)
        return SimpleNamespace(status_code=502)

    service_client = SimpleNamespace(request=fake_request)

    selected = asyncio.run(route_manager.select_healthy_upstream("primary", service_client))
    assert selected == "https://fallback.example.com"
