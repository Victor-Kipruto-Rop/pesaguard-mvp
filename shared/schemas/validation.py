from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol


class SchemaValidator(Protocol):
    def validate(self, payload: Dict[str, Any]) -> bool:
        ...


class SimpleSchemaValidator:
    """A lightweight validator driven by a schema definition."""

    def __init__(self, schema: Dict[str, Any]) -> None:
        self.schema = schema

    def validate(self, payload: Dict[str, Any]) -> bool:
        for field_name, rules in self.schema.items():
            if rules.get("required") and field_name not in payload:
                return False
            if field_name in payload:
                expected_type = rules.get("type")
                if expected_type == "string" and not isinstance(payload[field_name], str):
                    return False
                if expected_type == "integer" and not isinstance(payload[field_name], int):
                    return False
                if expected_type == "boolean" and not isinstance(payload[field_name], bool):
                    return False
        return True


class SerializationAdapter:
    """A helper that converts values into a canonical JSON-friendly format."""

    @staticmethod
    def to_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return {str(key): SerializationAdapter.to_dict(item) for key, item in value.items()}
        if isinstance(value, list):
            return [SerializationAdapter.to_dict(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
