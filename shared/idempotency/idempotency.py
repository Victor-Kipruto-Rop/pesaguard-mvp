from __future__ import annotations

from typing import Any, Dict


class IdempotencyStore:
    """A simple in-process idempotency store for repeated requests."""

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}

    def record(self, key: str, payload: Dict[str, Any]) -> bool:
        if key in self._records:
            return False
        self._records[key] = payload
        return True
