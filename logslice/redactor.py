"""Log line redaction — masks sensitive patterns before output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class RedactRule:
    pattern: str
    replacement: str = "[REDACTED]"
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            self._compiled = re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(f"Invalid redact pattern {self.pattern!r}: {exc}") from exc

    def apply(self, line: str) -> Tuple[str, int]:
        """Return (redacted_line, substitution_count)."""
        result, count = self._compiled.subn(self.replacement, line)
        return result, count


@dataclass
class RedactorConfig:
    enabled: bool = True
    rules: List[RedactRule] = field(default_factory=list)


class LogRedactor:
    """Applies a sequence of redaction rules to log lines."""

    def __init__(self, config: Optional[RedactorConfig] = None) -> None:
        self._config = config or RedactorConfig()
        self._total_redactions: int = 0

    @property
    def config(self) -> RedactorConfig:
        return self._config

    @property
    def total_redactions(self) -> int:
        return self._total_redactions

    def process(self, line: str) -> str:
        """Return the line with all matching patterns replaced.

        Returns the original line unchanged when disabled or no rules
        are configured.
        """
        if not self._config.enabled or not self._config.rules:
            return line

        for rule in self._config.rules:
            line, count = rule.apply(line)
            self._total_redactions += count

        return line

    def reset_stats(self) -> None:
        """Reset the running redaction counter."""
        self._total_redactions = 0
