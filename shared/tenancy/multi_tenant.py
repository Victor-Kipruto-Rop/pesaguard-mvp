from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional


class TenantContext:
    """Tenant-aware request context for cross-tenant isolation."""

    _var = contextvars.ContextVar("tenant_context", default=None)

    def __init__(self, tenant_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.tenant_id = tenant_id
        self.metadata = metadata or {}

    @classmethod
    def current(cls) -> "TenantContext":
        value = cls._var.get()
        if value is None:
            value = TenantContext()
            cls._var.set(value)
        return value


@contextmanager
def tenant_context(tenant_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    previous = TenantContext._var.get()
    token = TenantContext._var.set(TenantContext(tenant_id=tenant_id, metadata=metadata or {}))
    try:
        yield
    finally:
        if previous is None:
            TenantContext._var.set(None)
        else:
            TenantContext._var.reset(token)
