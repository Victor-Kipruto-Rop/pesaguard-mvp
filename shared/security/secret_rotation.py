from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional


@dataclass(slots=True)
class SecretRotationPolicy:
    name: str
    rotate_every: timedelta
    last_rotated: datetime
    callback: Callable[[str], None]


class SecretRotationManager:
    """A simple secret rotation manager for environment-backed secrets."""

    def __init__(self, provider: Callable[[str], Optional[str]], setter: Callable[[str, str], None]) -> None:
        self.provider = provider
        self.setter = setter
        self._policies: Dict[str, SecretRotationPolicy] = {}

    def add_policy(self, policy: SecretRotationPolicy) -> None:
        self._policies[policy.name] = policy

    def rotate_if_needed(self) -> None:
        now = datetime.utcnow()
        for policy in self._policies.values():
            if now - policy.last_rotated >= policy.rotate_every:
                secret = secrets.token_hex(32)
                self.setter(policy.name, secret)
                policy.callback(policy.name)
                policy.last_rotated = now
