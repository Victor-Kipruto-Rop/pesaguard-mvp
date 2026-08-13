from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(slots=True)
class AuditEntry:
    event_type: str
    actor: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


class AuditLogger:
    """A lightweight audit trail for platform events."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def log(self, event_type: str, actor: str, payload: Optional[Dict[str, Any]] = None) -> AuditEntry:
        entry = AuditEntry(event_type=event_type, actor=actor, payload=payload or {}, timestamp=time.time())
        self._entries.append(entry)
        return entry

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def export_json(self) -> str:
        return json.dumps([entry.__dict__ for entry in self._entries], default=str)
