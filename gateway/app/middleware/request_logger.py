"""Compatibility export for request logging middleware."""
from app.middleware.request_context import RequestContextMiddleware

RequestLoggerMiddleware = RequestContextMiddleware

__all__ = ["RequestLoggerMiddleware"]
