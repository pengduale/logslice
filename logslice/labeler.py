from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class LabelRule:
    """A single pattern-to-label mapping."""
    pattern: str
    label: str
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._compiled = re.compile(self.pattern)

    def matches(self, line: str) -> bool:
        return bool(self._compiled.search(line))


@dataclass
class LabelerConfig:
    """Configuration for the log line labeler."""
    rules: list[LabelRule] = field(default_factory=list)
    enabled: bool = True
    default_label: Optional[str] = None


class LogLabeler:
    """Assigns a text label to a log line based on the first matching rule.

    Labels can be used downstream (e.g. in JSON output or highlighting)
    to categorise lines such as ERROR, WARNING, INFO, etc.
    """

    def __init__(self, config: LabelerConfig) -> None:
        self._config = config

    @property
    def config(self) -> LabelerConfig:
        return self._config

    def label_line(self, line: str) -> Optional[str]:
        """Return the label for *line*, or the default label if no rule matches.

        Returns ``None`` when the labeler is disabled and no default is set.
        """
        if not self._config.enabled:
            return self._config.default_label

        for rule in self._config.rules:
            if rule.matches(line):
                return rule.label

        return self._config.default_label

    def annotate(self, line: str) -> str:
        """Return *line* prefixed with ``[LABEL] `` when a label is found."""
        lbl = self.label_line(line)
        if lbl is None:
            return line
        return f"[{lbl}] {line}"
