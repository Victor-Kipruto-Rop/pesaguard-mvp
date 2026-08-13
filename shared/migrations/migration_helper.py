from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(slots=True)
class MigrationStep:
    name: str
    up: Callable[[], None]
    down: Callable[[], None]


class MigrationManager:
    """A basic migration helper for registering and applying migration steps."""

    def __init__(self) -> None:
        self._steps: List[MigrationStep] = []
        self._applied: List[str] = []

    def register(self, step: MigrationStep) -> None:
        self._steps.append(step)

    def apply_all(self) -> None:
        for step in self._steps:
            if step.name not in self._applied:
                step.up()
                self._applied.append(step.name)

    def rollback_all(self) -> None:
        for step in reversed(self._steps):
            if step.name in self._applied:
                step.down()
                self._applied.remove(step.name)

    def status(self) -> Dict[str, bool]:
        return {step.name: step.name in self._applied for step in self._steps}
