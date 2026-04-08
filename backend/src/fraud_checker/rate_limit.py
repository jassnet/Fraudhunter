from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitRule:
    limit: int
    window_seconds: int


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, rule: RateLimitRule) -> tuple[bool, int]:
        now = time.time()
        window_start = now - rule.window_seconds
        with self._lock:
            entries = self._events[key]
            while entries and entries[0] <= window_start:
                entries.popleft()
            if len(entries) >= rule.limit:
                retry_after = max(1, int(entries[0] + rule.window_seconds - now))
                return False, retry_after
            entries.append(now)
            return True, 0
