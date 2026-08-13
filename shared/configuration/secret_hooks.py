from __future__ import annotations

from typing import Any

from shared.configuration.interfaces import ConfigurationReloadHook, SecretProvider
from shared.configuration.config import AppConfig


class SecretManagerHook(ConfigurationReloadHook):
    """Resolve secret placeholders like ${secret:jwt} in configuration payloads."""

    def __init__(self, provider: SecretProvider) -> None:
        self.provider = provider

    def on_reload(self, config: AppConfig) -> None:
        return None

    def resolve_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._resolve_value(payload)

    def _resolve_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._resolve_string(value)
        if isinstance(value, list):
            return [self._resolve_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self._resolve_value(item) for key, item in value.items()}
        return value

    def _resolve_string(self, value: str) -> Any:
        prefix = "${secret:"
        suffix = "}"
        if value.startswith(prefix) and value.endswith(suffix):
            secret_key = value[len(prefix) : -len(suffix)]
            return self.provider.get_secret(secret_key)
        return value
