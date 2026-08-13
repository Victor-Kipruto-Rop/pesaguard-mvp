from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class LockLease:
    name: str
    owner: str
    acquired_at: float
    expires_at: float


class DistributedLockManager:
    """A lightweight in-process distributed lock manager for shared services."""

    def __init__(self, ttl_seconds: int = 30) -> None:
        self.ttl_seconds = ttl_seconds
        self._leases: Dict[str, LockLease] = {}
        self._lock = threading.RLock()

    def acquire(self, name: str, owner: str) -> bool:
        with self._lock:
            now = time.time()
            lease = self._leases.get(name)
            if lease and lease.expires_at > now:
                return False
            self._leases[name] = LockLease(name=name, owner=owner, acquired_at=now, expires_at=now + self.ttl_seconds)
            return True

    def release(self, name: str, owner: str) -> bool:
        with self._lock:
            lease = self._leases.get(name)
            if lease is None or lease.owner != owner:
                return False
            self._leases.pop(name, None)
            return True

    def is_locked(self, name: str) -> bool:
        with self._lock:
            lease = self._leases.get(name)
            if lease is None:
                return False
            if lease.expires_at <= time.time():
                self._leases.pop(name, None)
                return False
            return True
