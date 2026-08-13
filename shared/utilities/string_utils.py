from __future__ import annotations

import re
from typing import Optional


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return normalized or "item"


def mask_sensitive(value: str, visible_prefix: int = 8) -> str:
    if not value:
        return value
    if len(value) <= visible_prefix:
        return value
    return value[:visible_prefix] + ("*" * max(6, len(value) - visible_prefix))


def truncate(value: str, max_length: int, suffix: str = "...") -> str:
    if len(value) <= max_length:
        return value
    if max_length <= len(suffix):
        return suffix[:max_length]
    return value[: max_length - len(suffix)] + suffix
