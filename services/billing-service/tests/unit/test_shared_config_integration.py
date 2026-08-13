from __future__ import annotations

from app.config.settings import Settings


class FakeStore:
    def load(self) -> dict[str, object]:
        return {
            "app_name": "billing-service",
            "secret_key": "${secret:billing_jwt}",
            "database_url": "postgresql://db.example.local/billing",
            "payment_provider_url": "https://payments.example.test",
        }


class FakeSecretProvider:
    def get_secret(self, key: str) -> str:
        return {"billing_jwt": "billing-secret"}[key]


def test_billing_settings_use_shared_config_bridge() -> None:
    settings = Settings.from_env(store=FakeStore(), secret_provider=FakeSecretProvider())

    assert settings.app_name == "billing-service"
    assert settings.secret_key == "billing-secret"
    assert settings.payment_provider_url == "https://payments.example.test"
