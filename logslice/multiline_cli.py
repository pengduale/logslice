"""CLI helpers for the multi-line aggregation feature."""
from __future__ import annotations

import argparse

from logslice.multiline import MultilineConfig


def add_multiline_args(parser: argparse.ArgumentParser) -> None:
    """Register multi-line aggregation arguments on *parser*."""
    grp = parser.add_argument_group("multi-line aggregation")
    grp.add_argument(
        "--ml-start",
        metavar="PATTERN",
        default=None,
        help="Regex that marks the beginning of a new multi-line event.",
    )
    grp.add_argument(
        "--ml-cont",
        metavar="PATTERN",
        default=None,
        help="Regex that marks a continuation line inside a multi-line event.",
    )
    grp.add_argument(
        "--ml-max-lines",
        metavar="N",
        type=int,
        default=0,
        help="Maximum lines per aggregated event (0 = unlimited).",
    )
    grp.add_argument(
        "--ml-join",
        metavar="STR",
        default="\n",
        help="String used to join aggregated lines (default: newline).",
    )


def multiline_from_args(args: argparse.Namespace) -> MultilineConfig:
    """Build a :class:`MultilineConfig` from parsed CLI *args*."""
    enabled = bool(args.ml_start or args.ml_cont)
    return MultilineConfig(
        enabled=enabled,
        start_pattern=args.ml_start,
        continuation_pattern=args.ml_cont,
        max_lines=args.ml_max_lines,
        join_str=args.ml_join,
    )
