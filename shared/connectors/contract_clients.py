from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class ContractRequest:
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    payload: Optional[Dict[str, Any]] = None


class ContractClient:
    """A generic external contract client with JSON request/response handling."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def send(self, request: ContractRequest) -> Dict[str, Any]:
        payload = None
        headers = dict(request.headers or {})
        if request.payload is not None:
            payload = json.dumps(request.payload).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(f"{self.base_url}{request.url}", data=payload, headers=headers, method=request.method)
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode("utf-8")
            return {"status": response.status, "body": json.loads(body) if body else {}}
