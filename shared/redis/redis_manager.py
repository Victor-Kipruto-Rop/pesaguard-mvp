from __future__ import annotations

import json
import time
from typing import Any, Optional


class RedisManager:
    """A lightweight in-process Redis-like manager for shared service use."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, Optional[float]]] = {}

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        expires_at = None if ttl_seconds is None else time.time() + ttl_seconds
        self._store[key] = (value, expires_at)

    def get(self, key: str) -> Any:
        value, expires_at = self._store.get(key, (None, None))
        if expires_at is not None and time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def increment(self, key: str, amount: int = 1) -> int:
        current = self.get(key) or 0
        next_value = int(current) + amount
        self.set(key, next_value)
        return next_value

    def publish(self, channel: str, payload: Any) -> None:
        self._store[f"__pub__:{channel}"] = (json.dumps(payload), None)

    def subscribe(self, channel: str) -> Any:
        return self.get(f"__pub__:{channel}")
