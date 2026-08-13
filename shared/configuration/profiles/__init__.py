from __future__ import annotations

from copy import deepcopy
from typing import Any


class ProfileInheritanceHelper:
    """Resolve profile inheritance maps with optional base profile composition."""

    def __init__(self, profiles: dict[str, dict[str, Any]]) -> None:
        self.profiles = profiles

    def resolve(self, profile_name: str) -> dict[str, Any]:
        profile = self.profiles.get(profile_name)
        if not profile:
            raise KeyError(f"Unknown profile: {profile_name}")

        parent_name = profile.get("extends")
        if not parent_name:
            return deepcopy(profile)

        resolved_parent = self.resolve(parent_name)
        merged = deepcopy(resolved_parent)
        for key, value in profile.items():
            if key == "extends":
                continue
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return merged
