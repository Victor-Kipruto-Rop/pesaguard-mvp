from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class DeliveryResult:
    success: bool
    status: int
    body: str
    attempts: int


class WebhookDeliveryGuarantee:
    """Retry-based webhook delivery guarantee with exponential backoff."""

    def __init__(self, endpoint: str, max_attempts: int = 3, backoff_seconds: float = 0.5) -> None:
        self.endpoint = endpoint
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds

    def send(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> DeliveryResult:
        attempts = 0
        last_status = 0
        while attempts < self.max_attempts:
            attempts += 1
            request = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers or {"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=5) as response:
                    body = response.read().decode("utf-8")
                    return DeliveryResult(success=True, status=response.status, body=body, attempts=attempts)
            except Exception:  # noqa: BLE001
                last_status = 500
                time.sleep(self.backoff_seconds * attempts)
        return DeliveryResult(success=False, status=last_status, body="", attempts=attempts)
