"""Time-window filtering: keep only log lines whose embedded timestamp falls
within an optional [start, end] range."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# Common timestamp patterns found in log lines
_TS_PATTERNS = [
    r"(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)",
    r"(?P<ts>\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})",
]
_TS_RE = re.compile("|".join(_TS_PATTERNS))

_PARSE_FMTS = [
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S",
]


def _parse_ts(raw: str) -> Optional[datetime]:
    raw = raw.rstrip("Z")
    for fmt in _PARSE_FMTS:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


@dataclass
class TimeWindowConfig:
    enabled: bool = False
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    drop_unparsed: bool = False

    def __post_init__(self) -> None:
        if self.enabled and self.start is None and self.end is None:
            raise ValueError("TimeWindowConfig: at least one of start/end must be set when enabled")
        if self.start and self.end and self.start > self.end:
            raise ValueError("TimeWindowConfig: start must not be after end")


@dataclass
class TimeWindowResult:
    passed: bool
    timestamp: Optional[datetime] = None
    reason: str = ""


class LogTimeWindow:
    """Filter log lines by the timestamp embedded in the line text."""

    def __init__(self, config: TimeWindowConfig) -> None:
        self._cfg = config

    @property
    def config(self) -> TimeWindowConfig:
        return self._cfg

    def process(self, line: str) -> TimeWindowResult:
        if not self._cfg.enabled:
            return TimeWindowResult(passed=True, reason="disabled")

        m = _TS_RE.search(line)
        if not m:
            passed = not self._cfg.drop_unparsed
            return TimeWindowResult(passed=passed, reason="no_timestamp")

        raw = m.group("ts") or ""
        dt = _parse_ts(raw)
        if dt is None:
            passed = not self._cfg.drop_unparsed
            return TimeWindowResult(passed=passed, reason="unparseable")

        if self._cfg.start and dt < self._cfg.start:
            return TimeWindowResult(passed=False, timestamp=dt, reason="before_start")
        if self._cfg.end and dt > self._cfg.end:
            return TimeWindowResult(passed=False, timestamp=dt, reason="after_end")

        return TimeWindowResult(passed=True, timestamp=dt, reason="in_window")
