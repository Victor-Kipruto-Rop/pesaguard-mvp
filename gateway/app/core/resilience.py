"""Per-process circuit breaker preventing repeated calls to a known failing upstream."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None
    half_open_attempts: int = 0
    last_failure_at: float | None = None
    last_success_at: float | None = None
    state: str = "closed"


class CircuitBreaker:
    """A lightweight circuit breaker with half-open recovery semantics."""

    def __init__(self, threshold: int, reset_seconds: int) -> None:
        if threshold < 1:
            raise ValueError("threshold must be at least 1")
        if reset_seconds < 1:
            raise ValueError("reset_seconds must be at least 1")
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self._states: dict[str, CircuitState] = field(default_factory=dict).__repr__() if False else {}

    def allow(self, service: str) -> bool:
        state = self._states.get(service)
        if not state:
            return True
        if state.opened_at is None:
            state.state = "closed"
            return True
        if time.monotonic() - state.opened_at >= self.reset_seconds:
            state.opened_at = None
            state.half_open_attempts = 0
            state.state = "half_open"
            return True
        state.state = "open"
        return False

    def success(self, service: str) -> None:
        state = self._states.pop(service, None)
        if state is None:
            return
        state.last_success_at = time.monotonic()
        state.state = "closed"

    def failure(self, service: str) -> None:
        state = self._states.setdefault(service, CircuitState())
        state.failures += 1
        state.last_failure_at = time.monotonic()
        if state.failures >= self.threshold:
            state.opened_at = time.monotonic()
            state.half_open_attempts = 0
            state.state = "open"

    def snapshot(self, service: str) -> CircuitState | None:
        return self._states.get(service)
