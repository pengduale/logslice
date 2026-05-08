"""Log line filtering with include/exclude regex patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class FilterConfig:
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    ignore_case: bool = False


@dataclass
class LogMatch:
    line: str
    line_number: int
    source: str
    matched_patterns: List[str] = field(default_factory=list)
    context_tag: Optional[str] = None  # 'before', 'after', or None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "line_number": self.line_number,
            "source": self.source,
            "line": self.line,
            "matched_patterns": self.matched_patterns,
        }
        if self.context_tag is not None:
            d["context_tag"] = self.context_tag
        return d


class LogFilter:
    def __init__(self, config: FilterConfig) -> None:
        self._config = config
        flags = re.IGNORECASE if config.ignore_case else 0
        self._include = [
            re.compile(p, flags) for p in config.include_patterns
        ]
        self._exclude = [
            re.compile(p, flags) for p in config.exclude_patterns
        ]

    @property
    def config(self) -> FilterConfig:
        return self._config

    def match(self, line: str, line_number: int, source: str) -> Optional[LogMatch]:
        """Return a LogMatch if the line passes all filters, else None."""
        for exc in self._exclude:
            if exc.search(line):
                return None

        matched: List[str] = []
        if self._include:
            for inc in self._include:
                if inc.search(line):
                    matched.append(inc.pattern)
            if not matched:
                return None
        else:
            matched = []

        return LogMatch(
            line=line,
            line_number=line_number,
            source=source,
            matched_patterns=matched,
        )

    def is_excluded(self, line: str) -> bool:
        """Return True if the line matches any exclude pattern."""
        return any(exc.search(line) for exc in self._exclude)
