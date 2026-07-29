"""Utility helpers for request and response header normalization."""
from __future__ import annotations

from typing import Iterable


def normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Normalize header names to lower-case and remove empty values."""
    return {key.lower(): value for key, value in headers.items() if key and value is not None and value != ""}


def strip_sensitive_headers(headers: dict[str, str], sensitive: Iterable[str]) -> dict[str, str]:
    """Remove sensitive header names from a request or response header set."""
    normalized_sensitive = {item.lower() for item in sensitive}
    return {key: value for key, value in headers.items() if key.lower() not in normalized_sensitive}


def is_health_probe(path: str, public_paths: Iterable[str]) -> bool:
    """Detect whether a path is a gateway probe endpoint."""
    return path.rstrip("/") in {probe.rstrip("/") for probe in public_paths}
