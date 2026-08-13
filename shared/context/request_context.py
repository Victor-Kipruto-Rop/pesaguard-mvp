from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional


class RequestContext:
    """Request-scoped context propagation for metadata and correlation values."""

    _var = contextvars.ContextVar("request_context", default=None)

    def __init__(self, correlation_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.correlation_id = correlation_id
        self.metadata = metadata or {}

    @classmethod
    def current(cls) -> "RequestContext":
        value = cls._var.get()
        if value is None:
            value = RequestContext()
            cls._var.set(value)
        return value

    @classmethod
    def set(cls, context: "RequestContext") -> None:
        cls._var.set(context)


@contextmanager
def request_context(correlation_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    previous = RequestContext._var.get()
    token = RequestContext._var.set(RequestContext(correlation_id=correlation_id, metadata=metadata or {}))
    try:
        yield
    finally:
        if previous is None:
            RequestContext._var.set(None)
        else:
            RequestContext._var.reset(token)
