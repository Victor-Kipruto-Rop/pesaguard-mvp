from __future__ import annotations

from typing import Iterator


class Connection:
    """A minimal connection abstraction for local and pooled usage."""

    def __init__(self, name: str = "default") -> None:
        self.name = name

    def execute(self, statement: str) -> None:
        self._last_statement = statement


class ConnectionPool:
    """A simple pooled connection manager for shared infrastructure code."""

    def __init__(self, max_connections: int = 10) -> None:
        self.max_connections = max_connections
        self._connections = [Connection() for _ in range(min(max_connections, 1))]

    def acquire(self) -> "ConnectionPoolContext":
        return ConnectionPoolContext(self._connections[0])


class ConnectionPoolContext:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def __enter__(self) -> Connection:
        return self.connection

    def __exit__(self, exc_type, exc, tb) -> None:
        return None
