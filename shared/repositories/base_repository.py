from __future__ import annotations

from typing import Generic, List, Optional, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    def save(self, entity: T) -> T:
        ...

    def get_by_id(self, entity_id: str) -> Optional[T]:
        ...

    def list_all(self) -> List[T]:
        ...


class InMemoryRepository(Generic[T]):
    """A simple repository adapter backed by an in-memory store."""

    def __init__(self) -> None:
        self._store: dict[str, T] = {}

    def save(self, entity: T) -> T:
        entity_id = getattr(entity, "id", None)
        if entity_id is None:
            raise ValueError("entity must have an id attribute")
        self._store[str(entity_id)] = entity
        return entity

    def get_by_id(self, entity_id: str) -> Optional[T]:
        return self._store.get(entity_id)

    def list_all(self) -> List[T]:
        return list(self._store.values())
