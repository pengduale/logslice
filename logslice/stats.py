"""Statistics tracking for log filtering sessions."""
from dataclasses import dataclass, field
from typing import Dict, Optional
import time


@dataclass
class FilterStats:
    """Tracks statistics for a log filtering/tailing session."""
    total_lines: int = 0
    matched_lines: int = 0
    excluded_lines: int = 0
    start_time: float = field(default_factory=time.monotonic)
    end_time: Optional[float] = None
    pattern_hit_counts: Dict[str, int] = field(default_factory=dict)

    def record_line(self, matched: bool, excluded: bool = False, pattern: Optional[str] = None) -> None:
        """Record a processed line and update counters."""
        self.total_lines += 1
        if excluded:
            self.excluded_lines += 1
        elif matched:
            self.matched_lines += 1
            if pattern:
                self.pattern_hit_counts[pattern] = self.pattern_hit_counts.get(pattern, 0) + 1

    def finish(self) -> None:
        """Mark the session as complete and record end time."""
        self.end_time = time.monotonic()

    @property
    def elapsed_seconds(self) -> float:
        """Return elapsed time in seconds."""
        end = self.end_time if self.end_time is not None else time.monotonic()
        return round(end - self.start_time, 4)

    @property
    def match_rate(self) -> float:
        """Return the ratio of matched lines to total lines."""
        if self.total_lines == 0:
            return 0.0
        return round(self.matched_lines / self.total_lines, 4)

    def to_dict(self) -> dict:
        """Serialize stats to a plain dictionary."""
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "excluded_lines": self.excluded_lines,
            "elapsed_seconds": self.elapsed_seconds,
            "match_rate": self.match_rate,
            "pattern_hit_counts": dict(self.pattern_hit_counts),
        }

    def summary(self) -> str:
        """Return a human-readable summary string."""
        return (
            f"Lines: {self.total_lines} total, "
            f"{self.matched_lines} matched, "
            f"{self.excluded_lines} excluded "
            f"({self.match_rate:.1%} match rate) "
            f"in {self.elapsed_seconds}s"
        )
