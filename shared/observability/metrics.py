from __future__ import annotations

import time
from typing import Callable, Dict, Optional


class MetricsRegistry:
    """A simple in-process metrics registry for counters and timings."""

    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._timings: Dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + value

    def observe(self, name: str, value: float) -> None:
        self._timings.setdefault(name, []).append(value)

    def snapshot(self) -> Dict[str, object]:
        return {"counters": dict(self._counters), "timings": {k: list(v) for k, v in self._timings.items()}}


class Timer:
    def __init__(self, registry: MetricsRegistry, name: str) -> None:
        self.registry = registry
        self.name = name
        self.started_at = time.perf_counter()

    def stop(self) -> float:
        duration = time.perf_counter() - self.started_at
        self.registry.observe(self.name, duration)
        return duration


def timed(registry: MetricsRegistry, name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    import functools
    from typing import TypeVar

    T = TypeVar("T")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timer = Timer(registry, name)
            try:
                return func(*args, **kwargs)
            finally:
                timer.stop()
        return wrapper
    return decorator
