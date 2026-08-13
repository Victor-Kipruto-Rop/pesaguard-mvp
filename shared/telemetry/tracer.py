from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


class Span:
    """A minimal tracing span abstraction."""

    def __init__(self, name: str) -> None:
        self.name = name


@contextmanager
def trace_span(name: str) -> Iterator[Span]:
    span = Span(name)
    try:
        yield span
    finally:
        pass
