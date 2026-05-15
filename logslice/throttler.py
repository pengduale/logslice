"""Throttler: suppress repeated identical lines within a time window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ThrottlerConfig:
    enabled: bool = False
    window_seconds: float = 5.0
    max_repeats: int = 1

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.max_repeats < 1:
            raise ValueError("max_repeats must be at least 1")


@dataclass
class _LineState:
    count: int = 0
    first_seen: float = field(default_factory=time.monotonic)


class LogThrottler:
    """Suppress lines that repeat too frequently within a sliding window."""

    def __init__(self, config: Optional[ThrottlerConfig] = None) -> None:
        self._config = config or ThrottlerConfig()
        self._seen: Dict[str, _LineState] = {}

    @property
    def config(self) -> ThrottlerConfig:
        return self._config

    def process(self, line: str) -> Optional[str]:
        """Return the line if it should be emitted, None if throttled."""
        if not self._config.enabled:
            return line

        now = time.monotonic()
        state = self._seen.get(line)

        if state is None or (now - state.first_seen) >= self._config.window_seconds:
            self._seen[line] = _LineState(count=1, first_seen=now)
            return line

        state.count += 1
        if state.count <= self._config.max_repeats:
            return line

        return None

    def reset(self) -> None:
        """Clear all tracked line states."""
        self._seen.clear()

    @property
    def tracked_count(self) -> int:
        """Number of distinct lines currently tracked."""
        return len(self._seen)
