from __future__ import annotations

import os
from typing import Any

from shared.configuration.interfaces import ConfigurationStore


class VaultConfigurationStore(ConfigurationStore):
    """A lightweight Vault-style configuration store adapter for local/testing use."""

    def __init__(self, endpoint: str | None = None, *, client: Any | None = None) -> None:
        self.endpoint = endpoint or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.client = client or self._default_client()

    def load(self) -> dict[str, Any]:
        response = self.client.read(self.endpoint)
        if isinstance(response, dict):
            return response
        return {"config": response}

    def save(self, data: dict[str, Any]) -> None:
        self.client.write(self.endpoint, data)

    @staticmethod
    def _default_client() -> Any:
        class _LocalClient:
            def read(self, path: str) -> dict[str, Any]:
                return {}

            def write(self, path: str, data: dict[str, Any]) -> None:
                return None

        return _LocalClient()
