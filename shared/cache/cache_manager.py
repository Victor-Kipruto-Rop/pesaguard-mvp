from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: Optional[float] = None


class CacheManager:
    """A straightforward in-process cache with TTL support."""

    def __init__(self, default_ttl: int = 300) -> None:
        self.default_ttl = default_ttl
        self._store: Dict[str, CacheEntry] = {}

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = self.default_ttl if ttl_seconds is None else ttl_seconds
        expires_at = None if ttl is None else time.time() + ttl
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and time.time() >= entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value
