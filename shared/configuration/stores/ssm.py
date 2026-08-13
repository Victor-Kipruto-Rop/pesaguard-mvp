from __future__ import annotations

import os
from typing import Any

from shared.configuration.interfaces import ConfigurationStore


class SSMConfigurationStore(ConfigurationStore):
    """A simple AWS SSM/AppConfig-style adapter that can be backed by a fake client in tests."""

    def __init__(self, endpoint: str | None = None, *, client: Any | None = None) -> None:
        self.endpoint = endpoint or os.getenv("SSM_CONFIG_PATH", "/config/pesaguard")
        self.client = client or self._default_client()

    def load(self) -> dict[str, Any]:
        response = self.client.get_parameter(self.endpoint)
        if isinstance(response, dict):
            return response
        return {"config": response}

    def save(self, data: dict[str, Any]) -> None:
        self.client.put_parameter(self.endpoint, data)

    @staticmethod
    def _default_client() -> Any:
        class _LocalClient:
            def get_parameter(self, path: str) -> dict[str, Any]:
                return {}

            def put_parameter(self, path: str, data: dict[str, Any]) -> None:
                return None

        return _LocalClient()
