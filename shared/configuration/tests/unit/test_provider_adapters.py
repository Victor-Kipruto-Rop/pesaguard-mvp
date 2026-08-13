from __future__ import annotations

from shared.configuration.stores.ssm import SSMConfigurationStore
from shared.configuration.stores.vault import VaultConfigurationStore


class FakeVaultClient:
    def __init__(self) -> None:
        self.writes: list[tuple[str, dict]] = []

    def read(self, path: str) -> dict[str, str]:
        return {"app_name": "vault-backed"}

    def write(self, path: str, data: dict) -> None:
        self.writes.append((path, data))


class FakeSSMClient:
    def __init__(self) -> None:
        self.values: dict[str, dict] = {}

    def get_parameter(self, path: str) -> dict[str, str]:
        return {"app_name": "ssm-backed"}

    def put_parameter(self, path: str, data: dict) -> None:
        self.values[path] = data


def test_vault_store_adapter_round_trips_payloads() -> None:
    client = FakeVaultClient()
    store = VaultConfigurationStore("http://vault.example.test", client=client)

    payload = store.load()
    store.save({"app_name": "vault-updated"})

    assert payload["app_name"] == "vault-backed"
    assert client.writes[0][1]["app_name"] == "vault-updated"


def test_ssm_store_adapter_round_trips_payloads() -> None:
    client = FakeSSMClient()
    store = SSMConfigurationStore("/config/app", client=client)

    payload = store.load()
    store.save({"app_name": "ssm-updated"})

    assert payload["app_name"] == "ssm-backed"
    assert client.values["/config/app"]["app_name"] == "ssm-updated"
