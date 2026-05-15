"""Severity-based log level filtering for logslice."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class Level(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def parse(cls, name: str) -> "Level":
        """Parse a level by name (case-insensitive)."""
        try:
            return cls[name.upper()]
        except KeyError:
            raise ValueError(f"Unknown log level: {name!r}")


_DEFAULT_PATTERN = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)

_ALIASES: dict[str, Level] = {
    "WARN": Level.WARNING,
    "FATAL": Level.CRITICAL,
}


def _normalise(token: str) -> Level:
    upper = token.upper()
    if upper in _ALIASES:
        return _ALIASES[upper]
    return Level[upper]


@dataclass
class SeverityConfig:
    enabled: bool = False
    min_level: Level = Level.DEBUG
    max_level: Level = Level.CRITICAL
    pattern: re.Pattern = field(default_factory=lambda: _DEFAULT_PATTERN)

    def __post_init__(self) -> None:
        if self.min_level > self.max_level:
            raise ValueError(
                f"min_level ({self.min_level.name}) must be <= "
                f"max_level ({self.max_level.name})"
            )


class LogSeverityFilter:
    """Filters log lines by detected severity level."""

    def __init__(self, config: SeverityConfig) -> None:
        self._config = config

    @property
    def config(self) -> SeverityConfig:
        return self._config

    def detect_level(self, line: str) -> Optional[Level]:
        """Return the first severity level found in *line*, or None."""
        m = self._config.pattern.search(line)
        if m is None:
            return None
        try:
            return _normalise(m.group(1))
        except KeyError:
            return None

    def process(self, line: str) -> Optional[str]:
        """Return *line* if it passes the severity filter, else None."""
        if not self._config.enabled:
            return line
        level = self.detect_level(line)
        if level is None:
            return line  # pass through lines with no detectable level
        if self._config.min_level <= level <= self._config.max_level:
            return line
        return None
