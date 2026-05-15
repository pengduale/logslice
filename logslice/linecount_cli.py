"""CLI argument helpers for the line count/limit feature."""

from __future__ import annotations

import argparse
from typing import Optional

from logslice.linecount import LineCountConfig


def add_linecount_args(parser: argparse.ArgumentParser) -> None:
    """Register --head, --skip, and related flags on *parser*."""
    group = parser.add_argument_group("line count / limit")
    group.add_argument(
        "--head",
        metavar="N",
        type=int,
        default=None,
        help="Stop after emitting N matching lines.",
    )
    group.add_argument(
        "--skip",
        metavar="N",
        type=int,
        default=0,
        help="Skip the first N lines before processing (default: 0).",
    )


def linecount_from_args(args: argparse.Namespace) -> LineCountConfig:
    """Build a :class:`LineCountConfig` from parsed CLI arguments."""
    head: Optional[int] = getattr(args, "head", None)
    skip: int = getattr(args, "skip", 0) or 0

    enabled = head is not None or skip > 0
    return LineCountConfig(
        enabled=enabled,
        max_lines=head,
        offset=skip,
    )
