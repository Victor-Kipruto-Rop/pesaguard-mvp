from __future__ import annotations

from app.config.settings import Settings


class FakeStore:
    def load(self) -> dict[str, object]:
        return {
            "app_name": "billing-service",
            "secret_key": "${secret:jwt}",
            "database_url": "sqlite:///./auth-service.db",
        }


class FakeSecretProvider:
    def get_secret(self, key: str) -> str:
        return {"jwt": "super-secret"}[key]


def test_auth_settings_use_remote_store_and_secret_hook(monkeypatch) -> None:
    monkeypatch.delenv("AUTH_CONFIG_STORE_URL", raising=False)
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    settings = Settings.from_env(store=FakeStore(), secret_provider=FakeSecretProvider())

    assert settings.app_name == "billing-service"
    assert settings.secret_key == "super-secret"
    assert settings.database_url == "sqlite:///./auth-service.db"
