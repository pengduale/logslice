"""Pipeline that wires together filter, highlighter, formatter, and stats."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.filter import FilterConfig, LogFilter, LogMatch
from logslice.formatter import LogFormatter, OutputFormat
from logslice.highlighter import HighlightConfig, LogHighlighter
from logslice.stats import FilterStats


@dataclass
class PipelineConfig:
    """Aggregated configuration for the full processing pipeline."""

    filter_config: FilterConfig = field(default_factory=FilterConfig)
    output_format: OutputFormat = OutputFormat.PLAIN
    show_line_numbers: bool = True
    show_source: bool = True
    highlight_config: HighlightConfig = field(default_factory=HighlightConfig)
    source_name: str = ""


class LogPipeline:
    """Processes raw log lines through filter → highlight → format stages."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._filter = LogFilter(config.filter_config)
        self._highlighter = LogHighlighter(config.highlight_config)
        self._formatter = LogFormatter(
            fmt=config.output_format,
            show_line_numbers=config.show_line_numbers,
            show_source=config.show_source,
        )
        self.stats = FilterStats()

    # ------------------------------------------------------------------
    def process(self, lines: Iterable[str]) -> Iterator[str]:
        """Yield formatted output lines for every matched input line."""
        for raw_line in lines:
            line = raw_line.rstrip("\n")
            match: Optional[LogMatch] = self._filter.check(line)
            self.stats.record_line(match)
            if match is None:
                continue
            if self._config.source_name and not match.source:
                match = LogMatch(
                    line=match.line,
                    line_number=match.line_number,
                    source=self._config.source_name,
                    matched_patterns=match.matched_patterns,
                )
            highlighted = self._highlighter.highlight_line(match.line)
            display_match = LogMatch(
                line=highlighted,
                line_number=match.line_number,
                source=match.source,
                matched_patterns=match.matched_patterns,
            )
            yield self._formatter.format_match(display_match)

    def finish(self) -> None:
        """Signal that processing is complete (records end time in stats)."""
        self.stats.finish()
