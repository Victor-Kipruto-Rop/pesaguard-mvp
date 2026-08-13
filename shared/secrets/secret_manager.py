from __future__ import annotations

import os
import threading
from typing import Callable, Dict, Optional


class SecretManager:
    """A simple secret provider with environment override hooks."""

    def __init__(self, provider: Optional[Callable[[str], Optional[str]]] = None) -> None:
        self._provider = provider
        self._cache: Dict[str, str] = {}
        self._lock = threading.RLock()

    def get(self, name: str) -> Optional[str]:
        with self._lock:
            if name in self._cache:
                return self._cache[name]
            value = None
            if self._provider is not None:
                value = self._provider(name)
            if value is None:
                value = os.getenv(name)
            if value is not None:
                self._cache[name] = value
            return value

    def set(self, name: str, value: str) -> None:
        with self._lock:
            self._cache[name] = value
