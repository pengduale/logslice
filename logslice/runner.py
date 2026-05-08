"""High-level entry-point that wires Reader + Pipeline together."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from logslice.pipeline import LogPipeline, PipelineConfig
from logslice.reader import LogReader
from logslice.stats import FilterStats


@dataclass
class RunConfig:
    """Top-level configuration consumed by :func:`run_pipeline`."""

    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    path: Optional[Path] = None
    print_stats: bool = False


def run_pipeline(config: RunConfig) -> FilterStats:
    """Read *path* (or stdin), process through the pipeline, print results.

    Returns the :class:`~logslice.stats.FilterStats` collected during the run.
    """
    reader = LogReader(path=config.path)

    # Inject the source name so formatters can display it.
    if not config.pipeline.source_name:
        config.pipeline.source_name = reader.source_name

    pipeline = LogPipeline(config.pipeline)

    try:
        for output_line in pipeline.process(reader.lines()):
            print(output_line)
    finally:
        pipeline.finish()

    if config.print_stats:
        _print_stats(pipeline.stats)

    return pipeline.stats


def _print_stats(stats: FilterStats) -> None:
    print(
        f"\n--- stats: {stats.matched_lines}/{stats.total_lines} lines matched "
        f"({stats.match_rate():.1%}) in {stats.elapsed_seconds():.3f}s ---"
    )
