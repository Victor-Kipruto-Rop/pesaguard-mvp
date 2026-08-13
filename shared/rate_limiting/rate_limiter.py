from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, DefaultDict


class SlidingWindowRateLimiter:
    """A simple sliding-window rate limiter for per-key traffic control."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: DefaultDict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self._requests[key]
        while bucket and now - bucket[0] >= self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True
