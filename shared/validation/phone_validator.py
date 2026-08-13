from __future__ import annotations

import re
from typing import Optional


def normalize_phone(value: str, *, country: Optional[str] = None) -> str:
    digits = re.sub(r"\D", "", value)
    if country and country.upper() == "KE":
        if digits.startswith("254"):
            return f"+{digits}"
        if digits.startswith("0") and len(digits) == 10:
            return f"+254{digits[1:]}"
        if len(digits) == 9:
            return f"+254{digits}"
    return f"+{digits}" if digits else ""


def is_valid_phone(value: str, *, country: Optional[str] = None) -> bool:
    normalized = normalize_phone(value, country=country)
    if not normalized:
        return False
    if country and country.upper() == "KE":
        return bool(re.fullmatch(r"\+254[1-9]\d{8}", normalized))
    return bool(re.fullmatch(r"\+\d{8,15}", normalized))
