from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass(slots=True)
class SagaStep:
    name: str
    action: Callable[[], bool]
    compensation: Optional[Callable[[], None]] = None


class SagaOrchestrator:
    """A simple saga orchestrator with compensation support."""

    def __init__(self) -> None:
        self._steps: List[SagaStep] = []

    def add_step(self, step: SagaStep) -> None:
        self._steps.append(step)

    def execute(self) -> bool:
        for step in self._steps:
            if not step.action():
                self._compensate(step)
                return False
        return True

    def _compensate(self, current_step: SagaStep) -> None:
        for step in reversed(self._steps):
            if step is current_step:
                break
            if step.compensation is not None:
                step.compensation()
