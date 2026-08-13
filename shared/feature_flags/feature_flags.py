from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class FeatureFlag:
    name: str
    enabled: bool = False
    metadata: Optional[Dict[str, Any]] = None


class FeatureFlagClient:
    """A simple feature-flag registry for shared platform capabilities."""

    def __init__(self) -> None:
        self._flags: Dict[str, FeatureFlag] = {}

    def register(self, flag: FeatureFlag) -> None:
        self._flags[flag.name] = flag

    def is_enabled(self, name: str) -> bool:
        flag = self._flags.get(name)
        return bool(flag and flag.enabled)

    def set_enabled(self, name: str, enabled: bool) -> None:
        flag = self._flags.get(name)
        if flag is None:
            self._flags[name] = FeatureFlag(name=name, enabled=enabled)
        else:
            flag.enabled = enabled
