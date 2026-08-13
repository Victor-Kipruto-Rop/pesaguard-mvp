from __future__ import annotations

import json
from datetime import datetime, date
from typing import Any, Dict


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return str(value)


def to_json_string(value: Any) -> str:
    return json.dumps(to_jsonable(value), sort_keys=True)
