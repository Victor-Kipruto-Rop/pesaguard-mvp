from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(slots=True)
class OutboxEvent:
    event_type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class OutboxStore:
    """A minimal outbox pattern implementation for local transaction-safe publishing."""

    def __init__(self) -> None:
        self._events: List[OutboxEvent] = []

    def add(self, event: OutboxEvent) -> None:
        self._events.append(event)

    def drain(self) -> List[OutboxEvent]:
        events = list(self._events)
        self._events.clear()
        return events
