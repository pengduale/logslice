"""End-to-end processing pipeline for log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from logslice.context import ContextCollector, ContextConfig
from logslice.deduplicator import DeduplicatorConfig, LogDeduplicator
from logslice.filter import FilterConfig, LogFilter, LogMatch
from logslice.formatter import LogFormatter, OutputFormat
from logslice.highlighter import HighlightConfig, LogHighlighter
from logslice.labeler import LabelerConfig, LogLabeler
from logslice.ratelimiter import LogRateLimiter, RateLimiterConfig
from logslice.redactor import LogRedactor, RedactorConfig
from logslice.sampler import LogSampler, SamplerConfig
from logslice.splitter import LogSplitter, SplitterConfig
from logslice.stats import FilterStats
from logslice.transformer import LogTransformer, TransformerConfig
from logslice.truncator import LogTruncator, TruncatorConfig


@dataclass
class PipelineConfig:
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    output_format: OutputFormat = OutputFormat.PLAIN
    show_line_numbers: bool = True
    show_source: bool = True
    highlight: HighlightConfig = field(default_factory=HighlightConfig)
    deduplicator: DeduplicatorConfig = field(default_factory=DeduplicatorConfig)
    sampler: SamplerConfig = field(default_factory=SamplerConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    truncator: TruncatorConfig = field(default_factory=TruncatorConfig)
    ratelimiter: RateLimiterConfig = field(default_factory=RateLimiterConfig)
    labeler: LabelerConfig = field(default_factory=LabelerConfig)
    redactor: RedactorConfig = field(default_factory=RedactorConfig)
    transformer: TransformerConfig = field(default_factory=TransformerConfig)
    splitter: SplitterConfig = field(default_factory=SplitterConfig)


class LogPipeline:
    """Chains all processing stages and yields formatted output lines."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._stats = FilterStats()
        filter_cfg = FilterConfig(
            include_patterns=config.include_patterns,
            exclude_patterns=config.exclude_patterns,
        )
        self._filter = LogFilter(filter_cfg)
        self._formatter = LogFormatter(
            fmt=config.output_format,
            show_line_numbers=config.show_line_numbers,
            show_source=config.show_source,
        )
        self._highlighter = LogHighlighter(config.highlight)
        self._deduplicator = LogDeduplicator(config.deduplicator)
        self._sampler = LogSampler(config.sampler)
        self._context = ContextCollector(config.context)
        self._truncator = LogTruncator(config.truncator)
        self._ratelimiter = LogRateLimiter(config.ratelimiter)
        self._labeler = LogLabeler(config.labeler)
        self._redactor = LogRedactor(config.redactor)
        self._transformer = LogTransformer(config.transformer)
        self._splitter = LogSplitter(config.splitter)

    @property
    def stats(self) -> FilterStats:
        return self._stats

    def process(self, lines: Iterator[tuple[str, int, str]]) -> Iterator[str]:
        """Process ``(source, line_number, text)`` tuples and yield output."""
        for source, lineno, raw in lines:
            # --- pre-filter transforms ---
            text = self._redactor.redact(raw)
            text = self._transformer.transform(text)
            text = self._truncator.truncate(text)

            # --- filtering ---
            match: Optional[LogMatch] = self._filter.match(source, lineno, text)
            if match is None:
                self._stats.record_line(matched=False, excluded=False)
                continue
            if match.excluded:
                self._stats.record_line(matched=False, excluded=True)
                continue

            self._stats.record_line(matched=True, excluded=False)

            # --- post-filter stages ---
            if not self._ratelimiter.allow():
                continue
            if not self._sampler.sample():
                continue

            dedup_result = self._deduplicator.process(match.line)
            if dedup_result is None:
                continue
            match = LogMatch(
                source=match.source,
                line_number=match.line_number,
                line=dedup_result,
                matched_patterns=match.matched_patterns,
                excluded=match.excluded,
            )

            # --- labeling / field splitting (metadata, not altering output here) ---
            _label = self._labeler.label(match.line)
            _fields = self._splitter.split(match.line)

            # --- context expansion ---
            for ctx_match in self._context.process(match):
                formatted = self._formatter.format_match(ctx_match)
                highlighted = self._highlighter.highlight_line(formatted)
                yield highlighted
