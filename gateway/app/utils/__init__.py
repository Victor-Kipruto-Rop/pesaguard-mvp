"""Pure utility functions for gateway extensions."""

from .headers import is_health_probe, normalize_headers, strip_sensitive_headers

__all__ = ["is_health_probe", "normalize_headers", "strip_sensitive_headers"]
