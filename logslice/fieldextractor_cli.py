"""CLI helpers for the field-extractor feature."""
from __future__ import annotations

import argparse
from typing import List

from logslice.fieldextractor import FieldExtractorConfig


def add_fieldextractor_args(parser: argparse.ArgumentParser) -> None:
    """Register field-extractor arguments on *parser*."""
    grp = parser.add_argument_group("field extraction")
    grp.add_argument(
        "--extract",
        dest="extract_patterns",
        metavar="PATTERN",
        action="append",
        default=[],
        help=(
            "Regex with named groups (e.g. '(?P<level>\\w+)') used to extract "
            "fields from each line.  May be supplied multiple times."
        ),
    )
    grp.add_argument(
        "--extract-all",
        dest="extract_all",
        action="store_true",
        default=False,
        help="Apply ALL extraction patterns instead of stopping at the first match.",
    )


def fieldextractor_from_args(args: argparse.Namespace) -> FieldExtractorConfig:
    """Build a :class:`FieldExtractorConfig` from parsed CLI *args*."""
    patterns: List[str] = args.extract_patterns or []
    enabled = bool(patterns)
    return FieldExtractorConfig(enabled=enabled, patterns=patterns)
