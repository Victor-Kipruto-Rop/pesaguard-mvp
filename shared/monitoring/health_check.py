from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional


@dataclass(slots=True)
class HealthCheckResult:
    name: str
    status: str
    details: Optional[dict] = None
    error: Optional[str] = None


class HealthCheckRegistry:
    """A small registry for service health checks with resilient execution."""

    def __init__(self) -> None:
        self._checks: Dict[str, Callable[[], Dict[str, object]]] = {}

    def add_check(self, name: str, check: Callable[[], Dict[str, object]]) -> None:
        self._checks[name] = check

    def run_all(self) -> Dict[str, HealthCheckResult]:
        results: Dict[str, HealthCheckResult] = {}
        for name, check in self._checks.items():
            try:
                payload = check()
                results[name] = HealthCheckResult(name=name, status="ok", details=payload)
            except Exception as exc:  # noqa: BLE001
                results[name] = HealthCheckResult(name=name, status="unhealthy", error=str(exc))
        return results
