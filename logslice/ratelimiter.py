from dataclasses import dataclass, field
from collections import deque
from time import monotonic
from typing import Optional


@dataclass
class RateLimiterConfig:
    enabled: bool = False
    max_lines_per_second: float = 100.0
    window_seconds: float = 1.0

    def __post_init__(self) -> None:
        if self.max_lines_per_second <= 0:
            raise ValueError("max_lines_per_second must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")


class LogRateLimiter:
    """Drops log lines that exceed a maximum throughput rate.

    Uses a sliding window to count lines emitted in the last
    `window_seconds` seconds and suppresses lines that would push
    the rate above `max_lines_per_second`.
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None) -> None:
        self._config = config or RateLimiterConfig()
        self._timestamps: deque = deque()
        self._dropped: int = 0
        self._passed: int = 0

    @property
    def config(self) -> RateLimiterConfig:
        return self._config

    @property
    def dropped(self) -> int:
        return self._dropped

    @property
    def passed(self) -> int:
        return self._passed

    def _evict_old(self, now: float) -> None:
        cutoff = now - self._config.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def process(self, line: str) -> Optional[str]:
        """Return the line if within rate limit, else None."""
        if not self._config.enabled:
            self._passed += 1
            return line

        now = monotonic()
        self._evict_old(now)

        limit = self._config.max_lines_per_second * self._config.window_seconds
        if len(self._timestamps) >= limit:
            self._dropped += 1
            return None

        self._timestamps.append(now)
        self._passed += 1
        return line
