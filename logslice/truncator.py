"""Line truncation support for logslice output."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TruncatorConfig:
    enabled: bool = False
    max_length: int = 200
    ellipsis: str = "..."

    def __post_init__(self) -> None:
        if self.max_length < 1:
            raise ValueError(f"max_length must be at least 1, got {self.max_length}")
        if len(self.ellipsis) >= self.max_length:
            raise ValueError(
                f"ellipsis length ({len(self.ellipsis)}) must be less than max_length ({self.max_length})"
            )


class LogTruncator:
    """Truncates long lines to a configurable maximum length."""

    def __init__(self, config: Optional[TruncatorConfig] = None) -> None:
        self._config = config or TruncatorConfig()

    @property
    def config(self) -> TruncatorConfig:
        return self._config

    def process(self, line: str) -> str:
        """Return the line, truncated if necessary.

        If truncation is disabled or the line fits within max_length,
        the original line is returned unchanged.
        """
        if not self._config.enabled:
            return line

        max_len = self._config.max_length
        if len(line) <= max_len:
            return line

        cut = max_len - len(self._config.ellipsis)
        return line[:cut] + self._config.ellipsis

    def was_truncated(self, original: str) -> bool:
        """Return True if the given line would be truncated under current config."""
        if not self._config.enabled:
            return False
        return len(original) > self._config.max_length
