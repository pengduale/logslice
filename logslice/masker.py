"""Pattern-based line masking — replace sensitive substrings with a fixed mask string."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MaskRule:
    pattern: str
    mask: str = "***"
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            self._compiled = re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(f"Invalid mask pattern {self.pattern!r}: {exc}") from exc

    def apply(self, line: str) -> str:
        assert self._compiled is not None
        return self._compiled.sub(self.mask, line)


@dataclass
class MaskerConfig:
    enabled: bool = False
    rules: List[MaskRule] = field(default_factory=list)


class LogMasker:
    """Apply a sequence of MaskRules to each line."""

    def __init__(self, config: MaskerConfig) -> None:
        self._config = config

    @property
    def config(self) -> MaskerConfig:
        return self._config

    def process(self, line: str) -> str:
        """Return *line* with all mask rules applied, or unchanged if disabled."""
        if not self._config.enabled:
            return line
        for rule in self._config.rules:
            line = rule.apply(line)
        return line

    def process_many(self, lines: List[str]) -> List[str]:
        return [self.process(l) for l in lines]
