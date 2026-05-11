from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterator, Optional

from logslice.filter import FilterConfig, LogFilter
from logslice.formatter import OutputFormat, LogFormatter
from logslice.highlighter import HighlightConfig, LogHighlighter
from logslice.stats import FilterStats
from logslice.labeler import LabelerConfig, LabelRule, LogLabeler


@dataclass
class PipelineConfig:
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    output_format: OutputFormat = OutputFormat.PLAIN
    show_line_numbers: bool = True
    show_source: bool = True
    highlight_pattern: Optional[str] = None
    highlight_color: str = "red"
    highlight_bold: bool = False
    label_rules: list[tuple[str, str]] = field(default_factory=list)
    default_label: Optional[str] = None


class LogPipeline:
    """Orchestrates filter → label → format → highlight for a stream of lines."""

    def __init__(self, config: PipelineConfig, source: str = "<input>") -> None:
        self._config = config
        self._source = source
        self._stats = FilterStats()

        self._filter = LogFilter(
            FilterConfig(
                include_patterns=config.include_patterns,
                exclude_patterns=config.exclude_patterns,
            )
        )
        self._formatter = LogFormatter(
            output_format=config.output_format,
            show_line_numbers=config.show_line_numbers,
            show_source=config.show_source,
        )
        self._highlighter = LogHighlighter(
            HighlightConfig(
                pattern=config.highlight_pattern,
                color=config.highlight_color,
                bold=config.highlight_bold,
                enabled=config.highlight_pattern is not None,
            )
        )
        rules = [LabelRule(pat, lbl) for pat, lbl in config.label_rules]
        self._labeler = LogLabeler(
            LabelerConfig(
                rules=rules,
                enabled=bool(rules),
                default_label=config.default_label,
            )
        )

    @property
    def stats(self) -> FilterStats:
        return self._stats

    def process(self, lines: Iterator[str]) -> Iterator[str]:
        for lineno, raw in enumerate(lines, start=1):
            line = raw.rstrip("\n")
            match = self._filter.match(line, source=self._source, line_number=lineno)
            self._stats.record_line(matched=match is not None, excluded=False)
            if match is None:
                continue
            label = self._labeler.label_line(line)
            if label:
                match = match._replace(line=f"[{label}] {match.line}")
            formatted = self._formatter.format_match(match)
            yield self._highlighter.highlight_line(formatted)

    def finish(self) -> None:
        self._stats.finish()
