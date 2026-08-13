from __future__ import annotations

from typing import Any, Dict


def validate_payload(payload: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> bool:
    for field_name, rules in schema.items():
        if rules.get("required") and field_name not in payload:
            return False
        if field_name in payload and rules.get("type") == "string" and not isinstance(payload[field_name], str):
            return False
        if field_name in payload and rules.get("type") == "integer" and not isinstance(payload[field_name], int):
            return False
    return True
