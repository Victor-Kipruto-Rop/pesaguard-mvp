from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Iterator, Optional


class CorrelationContext:
    """Stores correlation IDs for request-scoped operations."""

    _context_var = contextvars.ContextVar("correlation_context", default=None)

    @classmethod
    def current(cls) -> "CorrelationContext":
        value = cls._context_var.get()
        if value is None:
            value = CorrelationContext()
            cls._context_var.set(value)
        return value

    def __init__(self, correlation_id: Optional[str] = None) -> None:
        self.correlation_id = correlation_id


@contextmanager
def correlation_id(correlation_id_value: str) -> Iterator[None]:
    previous = CorrelationContext._context_var.get()
    token = CorrelationContext._context_var.set(CorrelationContext(correlation_id_value))
    try:
        yield
    finally:
        if previous is None:
            CorrelationContext._context_var.set(None)
        else:
            CorrelationContext._context_var.reset(token)
