from __future__ import annotations

from typing import Any

from shared.configuration.interfaces import SecretProvider


class EnvironmentSecretProvider(SecretProvider):
    """Resolve secrets from environment variables."""

    def __init__(self, prefix: str = "PESAGUARD_") -> None:
        self.prefix = prefix

    def get_secret(self, key: str) -> str:
        return __import__("os").environ[self.prefix + key]


class CompositeSecretProvider(SecretProvider):
    """Try multiple providers in order until a secret is found."""

    def __init__(self, providers: list[SecretProvider]) -> None:
        self.providers = providers

    def get_secret(self, key: str) -> str:
        for provider in self.providers:
            try:
                return provider.get_secret(key)
            except KeyError:
                continue
            except Exception:
                continue
        raise KeyError(f"Secret not found: {key}")
