from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional


class TraceSpan:
    """A lightweight tracing span abstraction for request flow annotation."""

    def __init__(self, name: str, parent: Optional["TraceSpan"] = None) -> None:
        self.name = name
        self.parent = parent
        self.attributes: dict[str, str] = {}

    def set_attribute(self, key: str, value: str) -> None:
        self.attributes[key] = value


@contextmanager
def trace_span(name: str) -> Iterator[TraceSpan]:
    span = TraceSpan(name)
    try:
        yield span
    finally:
        pass
