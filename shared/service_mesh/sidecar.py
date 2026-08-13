from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class SidecarContract:
    service_name: str
    endpoints: Dict[str, str]
    metadata: Dict[str, str] = field(default_factory=dict)


class SidecarRegistry:
    """A minimal registry for service mesh sidecar contracts."""

    def __init__(self) -> None:
        self._contracts: Dict[str, SidecarContract] = {}

    def register(self, contract: SidecarContract) -> None:
        self._contracts[contract.service_name] = contract

    def resolve(self, service_name: str) -> Optional[SidecarContract]:
        return self._contracts.get(service_name)

    def list_all(self) -> List[SidecarContract]:
        return list(self._contracts.values())
