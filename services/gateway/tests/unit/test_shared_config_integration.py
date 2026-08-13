from __future__ import annotations

from app.config.settings import Settings


class FakeStore:
    def load(self) -> dict[str, object]:
        return {
            "app_name": "gateway-service",
            "api_host": "127.0.0.1",
            "api_port": 8081,
            "auth_service_url": "https://auth.example.test",
        }


def test_gateway_settings_use_shared_config_bridge() -> None:
    settings = Settings.from_env(store=FakeStore())

    assert settings.app_name == "gateway-service"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8081
