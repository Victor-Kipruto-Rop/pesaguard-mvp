from __future__ import annotations

from typing import Callable, List


class FilterBuilder:
    """Builds simple equality filters for list-based queries."""

    def __init__(self) -> None:
        self._conditions: List[Callable[[dict], bool]] = []

    def eq(self, field: str, value: object) -> "FilterBuilder":
        self._conditions.append(lambda item: item.get(field) == value)
        return self

    def build(self) -> Callable[[List[dict]], List[dict]]:
        def _filter(items: List[dict]) -> List[dict]:
            return [item for item in items if all(condition(item) for condition in self._conditions)]
        return _filter
