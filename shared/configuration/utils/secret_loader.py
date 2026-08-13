from __future__ import annotations

import os
from typing import Callable, Optional

from shared.configuration.constants import SENSITIVE_FIELDS
from shared.configuration.exceptions.config_exception import ConfigurationError


class SecretProvider:
    """Secure hook for retrieving secrets from runtime secret stores."""

    def __init__(self, provider: Optional[Callable[[str], Optional[str]]] = None) -> None:
        self.provider = provider or os.environ.get

    def get(self, key: str) -> str:
        result = self.provider(key)
        if result is None:
            raise ConfigurationError(f"Secret not found for key: {key}")
        return result


def load_dynamic_secret(key: str, provider: Optional[Callable[[str], Optional[str]]] = None) -> str:
    return SecretProvider(provider).get(key)
