from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable, Deque, DefaultDict, Dict, Any


class RateLimitMiddleware:
    """A simple in-process middleware for per-key request throttling."""

    def __init__(self, limit: int = 100, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: DefaultDict[str, Deque[float]] = defaultdict(deque)

    def __call__(self, request: Dict[str, Any], handler: Callable[[Dict[str, Any]], Any]) -> Any:
        key = request.get("client_id") or request.get("user_id") or "anonymous"
        now = time.time()
        bucket = self._requests[key]
        while bucket and now - bucket[0] >= self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            raise PermissionError("rate limit exceeded")
        bucket.append(now)
        return handler(request)
