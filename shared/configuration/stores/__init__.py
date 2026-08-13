from __future__ import annotations

from typing import Any

from shared.configuration.interfaces import ConfigurationStore


class HttpConfigurationStore(ConfigurationStore):
    """Simple HTTP-backed configuration store adapter for remote config sources."""

    def __init__(self, endpoint: str, *, client: Any | None = None) -> None:
        self.endpoint = endpoint
        self.client = client or self._default_client()

    def load(self) -> dict[str, Any]:
        response = self.client.get(self.endpoint)
        return response.get("config", {})

    def save(self, data: dict[str, Any]) -> None:
        self.client.put(self.endpoint, data)

    @staticmethod
    def _default_client() -> Any:
        import requests

        class _SimpleRequestsClient:
            def get(self, url: str) -> dict[str, Any]:
                return requests.get(url, timeout=5).json()

            def put(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
                return requests.put(url, json=data, timeout=5).json()

        return _SimpleRequestsClient()
