from __future__ import annotations

from dataclasses import dataclass
from time import sleep
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.1
    max_delay: float = 1.0


def retry_with_backoff(func: Callable[[], T], policy: RetryPolicy) -> T:
    last_error: Exception | None = None
    delay = policy.base_delay
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= policy.max_attempts:
                break
            sleep(min(delay, policy.max_delay))
            delay *= 2
    raise RuntimeError(f"operation failed after {policy.max_attempts} attempts") from last_error
