"""Structured-log processor that prevents common secrets and personal data from escaping."""
from typing import Any

SENSITIVE_KEYS = frozenset({"authorization", "cookie", "set-cookie", "password", "token", "secret", "api_key", "x-api-key", "pan", "cvv"})


def redact_sensitive_fields(_: Any, __: str, event: dict[str, Any]) -> dict[str, Any]:
    def scrub(value: Any, key: str | None = None) -> Any:
        if key and key.lower().replace("-", "_") in SENSITIVE_KEYS:
            return "[REDACTED]"
        if isinstance(value, dict):
            return {item_key: scrub(item_value, item_key) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value
    return scrub(event)
