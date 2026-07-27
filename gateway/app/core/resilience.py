"""Per-process circuit breaker preventing repeated calls to a known failing upstream."""
import time
from dataclasses import dataclass


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class CircuitBreaker:
    def __init__(self, threshold: int, reset_seconds: int) -> None:
        self.threshold, self.reset_seconds = threshold, reset_seconds
        self._states: dict[str, CircuitState] = {}

    def allow(self, service: str) -> bool:
        state = self._states.get(service)
        if not state or state.opened_at is None:
            return True
        if time.monotonic() - state.opened_at >= self.reset_seconds:
            state.opened_at = None
            state.failures = 0
            return True
        return False

    def success(self, service: str) -> None:
        self._states.pop(service, None)

    def failure(self, service: str) -> None:
        state = self._states.setdefault(service, CircuitState())
        state.failures += 1
        if state.failures >= self.threshold:
            state.opened_at = time.monotonic()
