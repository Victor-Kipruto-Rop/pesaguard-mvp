from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class CursorPage(Generic[T]):
    items: List[T]
    next_cursor: Optional[str] = None


class CursorPaginator(Generic[T]):
    """A generic cursor-based paginator for list-like data."""

    def __init__(self, page_size: int = 20) -> None:
        if page_size <= 0:
            raise ValueError("page_size must be positive")
        self.page_size = page_size

    def paginate(self, items: List[T], cursor: Optional[str] = None) -> CursorPage[T]:
        start = 0 if cursor is None else int(cursor)
        page_items = items[start : start + self.page_size]
        next_cursor = str(start + self.page_size) if start + self.page_size < len(items) else None
        return CursorPage(items=page_items, next_cursor=next_cursor)
