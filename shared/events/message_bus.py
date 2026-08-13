from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(slots=True)
class EventEnvelope:
    event_type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageBus:
    """A lightweight event-driven message bus for in-process dispatching."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[EventEnvelope], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[EventEnvelope], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, envelope: EventEnvelope) -> None:
        for handler in self._subscribers.get(envelope.event_type, []):
            handler(envelope)
