"""Deduplication support for log lines."""

from dataclasses import dataclass, field
from collections import OrderedDict
from typing import Optional


@dataclass
class DeduplicatorConfig:
    enabled: bool = False
    window_size: int = 100  # max unique lines to track
    show_count: bool = True  # annotate repeated lines with occurrence count


class LogDeduplicator:
    """Tracks recently seen log lines and suppresses duplicates.

    Uses an LRU-style ordered dict bounded by window_size to avoid
    unbounded memory growth on large log streams.
    """

    def __init__(self, config: Optional[DeduplicatorConfig] = None) -> None:
        self._config = config or DeduplicatorConfig()
        self._seen: OrderedDict[str, int] = OrderedDict()

    @property
    def config(self) -> DeduplicatorConfig:
        return self._config

    def process(self, line: str) -> Optional[str]:
        """Return the (possibly annotated) line, or None if it is a duplicate.

        A duplicate is any line whose stripped text has already been seen
        within the current window.  The first occurrence is always returned.
        Subsequent occurrences are suppressed; when show_count is True the
        first occurrence is re-emitted with an updated count annotation each
        time a new duplicate arrives so callers can see the running total.
        """
        if not self._config.enabled:
            return line

        key = line.rstrip("\n")

        if key in self._seen:
            self._seen[key] += 1
            self._seen.move_to_end(key)  # refresh recency
            if self._config.show_count:
                count = self._seen[key]
                return f"{key} [x{count}]\n" if line.endswith("\n") else f"{key} [x{count}]"
            return None  # suppress silently

        # New line — register it
        self._seen[key] = 1

        # Evict oldest entry when window is full
        if len(self._seen) > self._config.window_size:
            self._seen.popitem(last=False)

        return line

    def reset(self) -> None:
        """Clear the seen-line window."""
        self._seen.clear()

    @property
    def unique_count(self) -> int:
        """Number of distinct lines currently tracked in the window."""
        return len(self._seen)
