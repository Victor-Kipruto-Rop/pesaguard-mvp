from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(slots=True)
class SortSpec:
    field: str
    descending: bool = False


def sort_items(items: List[Dict[str, Any]], specs: List[SortSpec]) -> List[Dict[str, Any]]:
    if not specs:
        return list(items)
    sorted_items = list(items)
    for spec in reversed(specs):
        sorted_items.sort(key=lambda item: item.get(spec.field, 0), reverse=spec.descending)
    return sorted_items
