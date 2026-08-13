from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass(slots=True)
class WebhookEvent:
    event_type: str
    payload: Dict[str, Any]
    signature: Optional[str] = None


class WebhookDispatcher:
    """A simple webhook dispatcher with optional signature headers."""

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    def dispatch(self, event: WebhookEvent) -> Dict[str, Any]:
        headers = {}
        if event.signature:
            headers["X-Signature"] = event.signature
        body = json.dumps(event.payload).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            return {"status": response.status, "body": response.read().decode("utf-8")}
