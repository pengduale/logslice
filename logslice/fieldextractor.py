"""Field extraction from log lines using named regex groups."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FieldExtractorConfig:
    enabled: bool = False
    patterns: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for pat in self.patterns:
            try:
                compiled = re.compile(pat)
            except re.error as exc:
                raise ValueError(f"Invalid pattern {pat!r}: {exc}") from exc
            if not compiled.groupindex:
                raise ValueError(
                    f"Pattern {pat!r} has no named groups; use (?P<name>...) syntax"
                )


@dataclass
class ExtractionResult:
    matched: bool
    fields: Dict[str, str]
    pattern: Optional[str] = None


class LogFieldExtractor:
    """Extract named fields from a log line using a list of regex patterns.

    The first pattern that matches the line wins; extracted groups are
    returned as a dict.  If no pattern matches, an empty dict is returned.
    """

    def __init__(self, config: FieldExtractorConfig) -> None:
        self._config = config
        self._compiled: List[re.Pattern[str]] = [
            re.compile(p) for p in config.patterns
        ]

    @property
    def config(self) -> FieldExtractorConfig:
        return self._config

    def extract(self, line: str) -> ExtractionResult:
        """Return an ExtractionResult for *line*.

        When the extractor is disabled or no pattern matches, ``matched``
        is *False* and ``fields`` is empty.
        """
        if not self._config.enabled:
            return ExtractionResult(matched=False, fields={})

        for pat, compiled in zip(self._config.patterns, self._compiled):
            m = compiled.search(line)
            if m:
                return ExtractionResult(
                    matched=True,
                    fields={k: v or "" for k, v in m.groupdict().items()},
                    pattern=pat,
                )

        return ExtractionResult(matched=False, fields={})

    def extract_all(self, line: str) -> List[ExtractionResult]:
        """Return one ExtractionResult per matching pattern (all matches)."""
        if not self._config.enabled:
            return []

        results: List[ExtractionResult] = []
        for pat, compiled in zip(self._config.patterns, self._compiled):
            m = compiled.search(line)
            if m:
                results.append(
                    ExtractionResult(
                        matched=True,
                        fields={k: v or "" for k, v in m.groupdict().items()},
                        pattern=pat,
                    )
                )
        return results
