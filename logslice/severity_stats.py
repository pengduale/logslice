"""Per-level counters collected during a pipeline run."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict

from logslice.severity import Level, LogSeverityFilter, SeverityConfig


@dataclass
class SeverityStats:
    """Accumulates line counts broken down by detected severity level."""

    counts: Counter = field(default_factory=Counter)
    undetected: int = 0

    def record(self, line: str, detector: LogSeverityFilter) -> None:
        level = detector.detect_level(line)
        if level is None:
            self.undetected += 1
        else:
            self.counts[level] += 1

    def total(self) -> int:
        return sum(self.counts.values()) + self.undetected

    def as_dict(self) -> Dict[str, int]:
        result: Dict[str, int] = {lvl.name: self.counts.get(lvl, 0) for lvl in Level}
        result["UNDETECTED"] = self.undetected
        return result

    def summary_lines(self) -> list[str]:
        """Return human-readable summary rows, omitting zero-count levels."""
        rows = []
        for lvl in Level:
            cnt = self.counts.get(lvl, 0)
            if cnt:
                rows.append(f"  {lvl.name:<10} {cnt}")
        if self.undetected:
            rows.append(f"  {'UNDETECTED':<10} {self.undetected}")
        return rows


# Convenience: a detector that never filters (used purely for level detection)
_DETECTOR = LogSeverityFilter(SeverityConfig(enabled=False))


def make_stats_detector() -> LogSeverityFilter:
    """Return a pass-through filter suitable for level detection only."""
    return _DETECTOR
