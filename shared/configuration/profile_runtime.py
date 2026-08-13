from __future__ import annotations

from typing import Any

from shared.configuration.profiles import ProfileInheritanceHelper


class RuntimeProfileResolver:
    """Apply profile inheritance during runtime configuration resolution."""

    def __init__(self, profiles: dict[str, dict[str, Any]]) -> None:
        self.helper = ProfileInheritanceHelper(profiles)

    def resolve(self, profile_name: str) -> dict[str, Any]:
        return self.helper.resolve(profile_name)
