"""Core log filtering module with regex support for logslice."""

import re
from dataclasses import dataclass, field
from typing import Iterator, List, Optional


@dataclass
class FilterConfig:
    """Configuration for log filtering."""
    patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    max_lines: Optional[int] = None


@dataclass
class LogMatch:
    """Represents a matched log line with metadata."""
    line_number: int
    content: str
    matched_pattern: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "line_number": self.line_number,
            "content": self.content,
            "matched_pattern": self.matched_pattern,
        }


class LogFilter:
    """Filters log lines based on include/exclude regex patterns."""

    def __init__(self, config: FilterConfig):
        self.config = config
        flags = 0 if config.case_sensitive else re.IGNORECASE

        self._include = [
            re.compile(p, flags) for p in config.patterns
        ]
        self._exclude = [
            re.compile(p, flags) for p in config.exclude_patterns
        ]

    def _is_excluded(self, line: str) -> bool:
        return any(rx.search(line) for rx in self._exclude)

    def _match_pattern(self, line: str) -> Optional[str]:
        """Return the first matching include pattern, or None."""
        for rx in self._include:
            if rx.search(line):
                return rx.pattern
        return None

    def filter_lines(self, lines: Iterator[str]) -> Iterator[LogMatch]:
        """Yield LogMatch objects for lines that pass the filter."""
        count = 0
        for line_number, raw_line in enumerate(lines, start=1):
            if self.config.max_lines and count >= self.config.max_lines:
                break

            line = raw_line.rstrip("\n")

            if self._is_excluded(line):
                continue

            if self._include:
                matched = self._match_pattern(line)
                if matched is None:
                    continue
            else:
                matched = None

            yield LogMatch(line_number=line_number, content=line, matched_pattern=matched)
            count += 1
