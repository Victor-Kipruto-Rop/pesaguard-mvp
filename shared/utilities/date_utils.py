from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional


def as_utc(value: Optional[datetime] = None) -> datetime:
    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def format_timestamp(value: datetime, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    return as_utc(value).strftime(fmt)


def minutes_ago(value: datetime, minutes: int) -> datetime:
    return as_utc(value) - timedelta(minutes=minutes)
