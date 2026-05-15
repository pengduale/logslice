"""Multi-line log event aggregation.

Some log formats (e.g. Java stack traces, Python tracebacks) span multiple
lines.  This module groups consecutive lines into a single logical event so
that downstream filters and formatters see one complete record instead of
fragmented pieces.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, List, Optional


@dataclass
class MultilineConfig:
    """Configuration for multi-line aggregation."""

    enabled: bool = False
    # A line that matches *start_pattern* begins a new event.
    start_pattern: Optional[str] = None
    # A line that matches *continuation_pattern* is appended to the current event.
    continuation_pattern: Optional[str] = None
    # Maximum number of lines to aggregate into one event (0 = unlimited).
    max_lines: int = 0
    # Separator inserted between aggregated lines in the final output.
    join_str: str = "\n"

    def __post_init__(self) -> None:
        if not self.enabled:
            return
        if self.start_pattern is None and self.continuation_pattern is None:
            raise ValueError(
                "MultilineConfig requires at least one of "
                "start_pattern or continuation_pattern when enabled."
            )
        if self.max_lines < 0:
            raise ValueError("max_lines must be >= 0.")
        if self.start_pattern is not None:
            re.compile(self.start_pattern)
        if self.continuation_pattern is not None:
            re.compile(self.continuation_pattern)


class LogMultilineAggregator:
    """Aggregates consecutive log lines into multi-line events."""

    def __init__(self, config: MultilineConfig) -> None:
        self._config = config
        self._buf: List[str] = []
        self._start_re = (
            re.compile(config.start_pattern) if config.start_pattern else None
        )
        self._cont_re = (
            re.compile(config.continuation_pattern)
            if config.continuation_pattern
            else None
        )

    @property
    def config(self) -> MultilineConfig:
        return self._config

    def _is_start(self, line: str) -> bool:
        return self._start_re is not None and bool(self._start_re.search(line))

    def _is_continuation(self, line: str) -> bool:
        return self._cont_re is not None and bool(self._cont_re.search(line))

    def _flush(self) -> Optional[str]:
        if not self._buf:
            return None
        event = self._config.join_str.join(self._buf)
        self._buf = []
        return event

    def process(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield aggregated events from *lines*."""
        if not self._config.enabled:
            yield from lines
            return

        max_lines = self._config.max_lines

        for line in lines:
            if self._is_start(line):
                flushed = self._flush()
                if flushed is not None:
                    yield flushed
                self._buf.append(line)
            elif self._buf and self._is_continuation(line):
                if max_lines == 0 or len(self._buf) < max_lines:
                    self._buf.append(line)
                else:
                    yield self._flush()  # type: ignore[misc]
                    self._buf.append(line)
            else:
                flushed = self._flush()
                if flushed is not None:
                    yield flushed
                yield line

        flushed = self._flush()
        if flushed is not None:
            yield flushed
