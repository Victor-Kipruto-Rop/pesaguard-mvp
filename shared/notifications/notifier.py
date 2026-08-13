from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass(slots=True)
class Notification:
    recipient: str
    subject: str
    body: str


class NotificationService:
    """A simple notification abstraction with pluggable delivery handlers."""

    def __init__(self) -> None:
        self._handlers: List[Callable[[Notification], None]] = []

    def add_handler(self, handler: Callable[[Notification], None]) -> None:
        self._handlers.append(handler)

    def send(self, notification: Notification) -> None:
        for handler in self._handlers:
            handler(notification)
