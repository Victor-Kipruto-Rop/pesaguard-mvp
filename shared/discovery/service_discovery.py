from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class ServiceRegistration:
    name: str
    address: str
    metadata: Dict[str, str] = field(default_factory=dict)


class ServiceRegistry:
    """A lightweight service discovery registry for shared platform services."""

    def __init__(self) -> None:
        self._services: Dict[str, ServiceRegistration] = {}

    def register(self, registration: ServiceRegistration) -> None:
        self._services[registration.name] = registration

    def get(self, name: str) -> ServiceRegistration | None:
        return self._services.get(name)

    def list_all(self) -> List[ServiceRegistration]:
        return list(self._services.values())
