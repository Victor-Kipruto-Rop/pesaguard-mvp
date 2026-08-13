from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass(slots=True)
class ComplianceRule:
    name: str
    evaluator: Callable[[Dict[str, object]], bool]


class PolicyEnforcer:
    """A lightweight policy engine for compliance checks."""

    def __init__(self) -> None:
        self._rules: List[ComplianceRule] = []

    def add_rule(self, rule: ComplianceRule) -> None:
        self._rules.append(rule)

    def evaluate(self, context: Dict[str, object]) -> bool:
        return all(rule.evaluator(context) for rule in self._rules)
