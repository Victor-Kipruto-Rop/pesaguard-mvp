from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar("T")


class EnvironmentSettings:
    """A typed environment settings wrapper with safe casting."""

    def __init__(self, env: Optional[Dict[str, str]] = None) -> None:
        self._env = env or os.environ

    def get(self, key: str, default: Optional[Any] = None, *, cast: Optional[Callable[[str], T]] = None) -> Any:
        value = self._env.get(key)
        if value is None:
            return default
        if cast is None:
            return value
        if cast is bool:
            return value.lower() in {"1", "true", "yes", "on"}
        if cast is int:
            return int(value)
        if cast is float:
            return float(value)
        if cast is list:
            return [item.strip() for item in value.split(",") if item.strip()]
        return cast(value)
