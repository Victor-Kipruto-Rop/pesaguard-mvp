from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(slots=True)
class RuntimeContract:
    name: str
    version: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuntimeContractRegistry:
    """A simple registry for runtime contract descriptors used by services."""

    def __init__(self) -> None:
        self._contracts: Dict[str, RuntimeContract] = {}

    def register(self, contract: RuntimeContract) -> None:
        self._contracts[contract.name] = contract

    def get(self, name: str) -> RuntimeContract | None:
        return self._contracts.get(name)

    def list_all(self) -> List[RuntimeContract]:
        return list(self._contracts.values())
