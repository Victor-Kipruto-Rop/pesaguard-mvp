from __future__ import annotations

import time
from enum import Enum
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """A simple circuit breaker that opens after repeated failures."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: int = 10) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at: Optional[float] = None

    def call(self, func: Callable[[], T]) -> T:
        if self.state == CircuitState.OPEN:
            if self.opened_at is not None and time.time() - self.opened_at < self.recovery_timeout_seconds:
                raise RuntimeError("circuit breaker is open")
            self.state = CircuitState.HALF_OPEN

        try:
            result = func()
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_at = time.time()
            raise
        else:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            return result
