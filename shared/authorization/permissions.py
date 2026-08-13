from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass(slots=True)
class Permission:
    name: str


@dataclass(slots=True)
class Role:
    name: str
    permissions: Set[str] = field(default_factory=set)


class PermissionRegistry:
    """A simple role-based permission registry that can be shared across services."""

    def __init__(self) -> None:
        self._roles: Dict[str, Role] = {}

    def register_role(self, role: Role) -> None:
        self._roles[role.name] = role

    def grant_permission(self, role_name: str, permission_name: str) -> None:
        role = self._roles.get(role_name)
        if role is None:
            raise KeyError(f"role '{role_name}' not found")
        role.permissions.add(permission_name)

    def has_permission(self, role_name: str, permission_name: str) -> bool:
        role = self._roles.get(role_name)
        if role is None:
            return False
        return permission_name in role.permissions
