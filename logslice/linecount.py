"""Line count tracking and limiting for log processing pipelines."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LineCountConfig:
    enabled: bool = False
    max_lines: Optional[int] = None
    offset: int = 0

    def __post_init__(self) -> None:
        if self.max_lines is not None and self.max_lines < 1:
            raise ValueError("max_lines must be a positive integer")
        if self.offset < 0:
            raise ValueError("offset must be >= 0")


@dataclass
class LineCountResult:
    line: str
    line_number: int
    stopped: bool = False


class LogLineCounter:
    """Tracks absolute line numbers and enforces optional line limits."""

    def __init__(self, config: LineCountConfig) -> None:
        self._config = config
        self._count: int = 0
        self._emitted: int = 0

    @property
    def config(self) -> LineCountConfig:
        return self._config

    @property
    def total_seen(self) -> int:
        return self._count

    @property
    def total_emitted(self) -> int:
        return self._emitted

    def process(self, line: str) -> Optional[LineCountResult]:
        """Return a LineCountResult or None if the line is skipped/limit reached."""
        self._count += 1

        if not self._config.enabled:
            self._emitted += 1
            return LineCountResult(line=line, line_number=self._count)

        if self._count <= self._config.offset:
            return None

        if self._config.max_lines is not None:
            if self._emitted >= self._config.max_lines:
                return LineCountResult(line=line, line_number=self._count, stopped=True)

        self._emitted += 1
        return LineCountResult(line=line, line_number=self._count)

    def reset(self) -> None:
        self._count = 0
        self._emitted = 0
