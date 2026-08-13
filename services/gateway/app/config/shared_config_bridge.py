from __future__ import annotations

from typing import Any

from shared.configuration.environment import detect_environment
from shared.configuration.profile_runtime import RuntimeProfileResolver
from shared.configuration.secret_hooks import SecretManagerHook


class SharedConfigBridge:
    """Adapts the shared configuration platform for gateway settings."""

    def __init__(self, store: Any | None = None, secret_provider: Any | None = None) -> None:
        self.store = store
        self.secret_provider = secret_provider

    def load_payload(self) -> dict[str, Any]:
        if self.store is None:
            return {}
        payload = self.store.load()
        return self._resolve_profiles(payload)

    def resolve_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.secret_provider is None:
            return payload
        hook = SecretManagerHook(self.secret_provider)
        return hook.resolve_payload(payload)

    def _resolve_profiles(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict) or "profiles" not in payload:
            return payload
        if not isinstance(payload["profiles"], dict):
            return payload

        active_profile = payload.get("active_profile")
        if not isinstance(active_profile, str):
            active_profile = payload.get("environment")
        if not isinstance(active_profile, str):
            active_profile = detect_environment().name.value

        resolved = RuntimeProfileResolver(payload["profiles"]).resolve(active_profile)
        result = {k: v for k, v in payload.items() if k not in {"profiles", "active_profile"}}
        return self._deep_merge(result, resolved)

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            if isinstance(merged.get(key), dict) and isinstance(value, dict):
                merged[key] = SharedConfigBridge._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
