"""Compatibility import for the payments route; routing is centrally registered in proxy."""
from app.routes.proxy import forward

__all__ = ["forward"]
