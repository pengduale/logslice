"""Line transformation module for logslice.

Supports applying regex-based substitutions to matched log lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TransformRule:
    pattern: str
    replacement: str
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            self._compiled = re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(f"Invalid transform pattern {self.pattern!r}: {exc}") from exc

    def apply(self, line: str) -> str:
        """Return *line* with all occurrences of *pattern* replaced by *replacement*."""
        return self._compiled.sub(self.replacement, line)


@dataclass
class TransformerConfig:
    enabled: bool = True
    rules: List[TransformRule] = field(default_factory=list)


class LogTransformer:
    """Applies a sequence of substitution rules to log lines."""

    def __init__(self, config: Optional[TransformerConfig] = None) -> None:
        self._config = config or TransformerConfig()

    @property
    def config(self) -> TransformerConfig:
        return self._config

    def process(self, line: str) -> str:
        """Return *line* after applying all configured transform rules in order.

        If the transformer is disabled or no rules are configured the original
        line is returned unchanged.
        """
        if not self._config.enabled or not self._config.rules:
            return line
        result = line
        for rule in self._config.rules:
            result = rule.apply(result)
        return result
