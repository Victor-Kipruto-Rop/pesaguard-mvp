from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen


class BaseHTTPClient:
    """A resilient HTTP client with retries and JSON decoding."""

    def __init__(self, retries: int = 3, backoff_factor: float = 0.25, timeout: int = 5) -> None:
        self.retries = max(retries, 0)
        self.backoff_factor = max(backoff_factor, 0.0)
        self.timeout = timeout

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        request = Request(url, method="GET", headers=headers or {})
        return self._request(request, timeout=timeout)

    def post(self, url: str, payload: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        body = json.dumps(payload or {}).encode("utf-8")
        request = Request(url, data=body, method="POST", headers={"Content-Type": "application/json", **(headers or {})})
        return self._request(request, timeout=timeout)

    def _request(self, request: Request, timeout: Optional[int] = None) -> Dict[str, Any]:
        last_error: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=timeout or self.timeout) as response:
                    body = response.read().decode("utf-8")
                    return json.loads(body)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(self.backoff_factor * (attempt + 1))
        raise RuntimeError(f"request failed after {self.retries + 1} attempts: {last_error}") from last_error
