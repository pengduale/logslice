"""Log line field splitter for structured extraction."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SplitterConfig:
    enabled: bool = False
    delimiter: Optional[str] = None
    regex: Optional[str] = None
    field_names: List[str] = field(default_factory=list)
    include_raw: bool = True

    def __post_init__(self) -> None:
        if self.enabled:
            if self.delimiter is None and self.regex is None:
                raise ValueError("SplitterConfig requires either 'delimiter' or 'regex'")
            if self.delimiter is not None and self.regex is not None:
                raise ValueError("SplitterConfig accepts 'delimiter' or 'regex', not both")
            if self.regex is not None:
                try:
                    re.compile(self.regex)
                except re.error as exc:
                    raise ValueError(f"Invalid splitter regex: {exc}") from exc


class LogSplitter:
    """Splits a log line into named or indexed fields."""

    def __init__(self, config: SplitterConfig) -> None:
        self._config = config
        self._pattern: Optional[re.Pattern] = (
            re.compile(config.regex) if config.enabled and config.regex else None
        )

    @property
    def config(self) -> SplitterConfig:
        return self._config

    def split(self, line: str) -> Optional[Dict[str, str]]:
        """Return a dict of extracted fields, or None if disabled.

        Keys are taken from ``field_names`` when provided, otherwise
        positional keys ``field_0``, ``field_1``, … are used.
        If ``include_raw`` is True a ``_raw`` key holds the original line.
        """
        if not self._config.enabled:
            return None

        if self._pattern is not None:
            m = self._pattern.search(line)
            if m:
                parts = list(m.groups()) if m.groups() else [m.group(0)]
            else:
                parts = []
        else:
            assert self._config.delimiter is not None
            parts = line.split(self._config.delimiter)

        names = self._config.field_names
        result: Dict[str, str] = {}
        for idx, value in enumerate(parts):
            key = names[idx] if idx < len(names) else f"field_{idx}"
            result[key] = value

        if self._config.include_raw:
            result["_raw"] = line

        return result
