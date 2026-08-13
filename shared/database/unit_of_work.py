from __future__ import annotations

from typing import Optional

from shared.database.connection_pool import ConnectionPool


class UnitOfWork:
    """A basic unit-of-work abstraction over a connection pool."""

    def __init__(self, connection_pool: ConnectionPool) -> None:
        self.connection_pool = connection_pool
        self.connection = None
        self._committed = False

    def __enter__(self) -> "UnitOfWork":
        self.connection = self.connection_pool.acquire().__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if not self._committed and exc_type is None:
                self.commit()
        finally:
            if self.connection is not None:
                self.connection_pool.acquire().__exit__(exc_type, exc, tb)
                self.connection = None

    def execute(self, statement: str) -> None:
        if self.connection is None:
            raise RuntimeError("unit of work is not active")
        self.connection.execute(statement)

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        self._committed = False
