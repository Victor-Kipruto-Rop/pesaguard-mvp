from __future__ import annotations

from pydantic import BaseModel

from shared.configuration.interfaces import SecretProvider
from shared.configuration.profiles import ProfileInheritanceHelper
from shared.configuration.schema_generation import ServiceConfigSchemaGenerator
from shared.configuration.stores import HttpConfigurationStore


class StaticSecretProvider(SecretProvider):
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def get_secret(self, key: str) -> str:
        return self.values[key]


class FakeHttpClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str, dict | None]] = []
        self.payload: dict | None = None

    def get(self, url: str):
        self.requests.append(("GET", url, None))
        return {"status": "ok", "config": {"app_name": "billing"}}

    def put(self, url: str, data: dict):
        self.requests.append(("PUT", url, data))
        self.payload = data
        return {"status": "ok"}


def test_remote_store_adapter_round_trips_payloads() -> None:
    client = FakeHttpClient()
    store = HttpConfigurationStore("https://example.test/config", client=client)

    data = store.load()
    assert data["app_name"] == "billing"

    store.save({"app_name": "payments"})
    assert client.payload == {"app_name": "payments"}
    assert client.requests[1][0] == "PUT"


def test_secret_manager_hook_resolves_secret_references() -> None:
    provider = StaticSecretProvider({"jwt": "super-secret"})
    payload = {"security": {"jwt_secret": "${secret:jwt}"}}

    resolved = provider.get_secret("jwt")
    assert resolved == "super-secret"


def test_profile_inheritance_helper_resolves_hierarchy() -> None:
    profiles = {
        "base": {"app": {"name": "pesaguard", "debug": False}, "database": {"host": "db"}},
        "development": {"extends": "base", "database": {"host": "localhost"}, "app": {"debug": True}},
    }

    helper = ProfileInheritanceHelper(profiles)
    resolved = helper.resolve("development")

    assert resolved["app"]["name"] == "pesaguard"
    assert resolved["app"]["debug"] is True
    assert resolved["database"]["host"] == "localhost"


def test_schema_generation_includes_service_metadata() -> None:
    class ServiceConfig(BaseModel):
        host: str
        port: int = 8080

    generator = ServiceConfigSchemaGenerator()
    schema = generator.generate(ServiceConfig, service_name="billing")

    assert schema["title"] == "BillingServiceConfig"
    assert schema["x-service-name"] == "billing"
    assert schema["properties"]["host"]["type"] == "string"
