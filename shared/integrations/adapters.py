from __future__ import annotations

from typing import Any, Callable, Dict, List


class IntegrationAdapter:
    """A small adapter pattern for event-driven integrations."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._handlers: List[Callable[[Dict[str, Any]], None]] = []

    def register_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        self._handlers.append(handler)

    def publish(self, event: Dict[str, Any]) -> None:
        for handler in self._handlers:
            handler(event)


class EventBusAdapter(IntegrationAdapter):
    """A concrete adapter specialized for event bus-style integrations."""

    pass
