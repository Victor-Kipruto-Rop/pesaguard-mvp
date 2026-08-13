from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass(slots=True)
class Message:
    recipient: str
    body: str


class EmailClient:
    """Simple email abstraction for shared platform services."""

    def __init__(self) -> None:
        self._handlers: List[Callable[[Message], None]] = []

    def add_handler(self, handler: Callable[[Message], None]) -> None:
        self._handlers.append(handler)

    def send(self, message: Message) -> None:
        for handler in self._handlers:
            handler(message)


class SMSClient:
    """Simple SMS abstraction for shared platform services."""

    def __init__(self) -> None:
        self._handlers: List[Callable[[Message], None]] = []

    def add_handler(self, handler: Callable[[Message], None]) -> None:
        self._handlers.append(handler)

    def send(self, message: Message) -> None:
        for handler in self._handlers:
            handler(message)
