"""CLI helpers for severity filtering arguments."""

from __future__ import annotations

import argparse

from logslice.severity import Level, LogSeverityFilter, SeverityConfig


def add_severity_args(parser: argparse.ArgumentParser) -> None:
    """Add severity-related arguments to *parser*."""
    grp = parser.add_argument_group("severity filtering")
    grp.add_argument(
        "--min-level",
        metavar="LEVEL",
        default=None,
        help="Minimum log level to include (DEBUG/INFO/WARNING/ERROR/CRITICAL).",
    )
    grp.add_argument(
        "--max-level",
        metavar="LEVEL",
        default=None,
        help="Maximum log level to include.",
    )


def severity_filter_from_args(args: argparse.Namespace) -> LogSeverityFilter:
    """Build a :class:`LogSeverityFilter` from parsed CLI *args*."""
    min_level_raw: str | None = getattr(args, "min_level", None)
    max_level_raw: str | None = getattr(args, "max_level", None)

    enabled = min_level_raw is not None or max_level_raw is not None

    min_level = Level.parse(min_level_raw) if min_level_raw else Level.DEBUG
    max_level = Level.parse(max_level_raw) if max_level_raw else Level.CRITICAL

    cfg = SeverityConfig(enabled=enabled, min_level=min_level, max_level=max_level)
    return LogSeverityFilter(cfg)
