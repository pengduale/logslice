"""CLI helpers for the masker module."""
from __future__ import annotations

import argparse
from typing import List

from logslice.masker import MaskRule, MaskerConfig


def add_masker_args(parser: argparse.ArgumentParser) -> None:
    """Register masker-related arguments on *parser*."""
    parser.add_argument(
        "--mask",
        metavar="PATTERN",
        action="append",
        dest="mask_patterns",
        default=[],
        help="Regex pattern whose matches are replaced with the mask string (repeatable).",
    )
    parser.add_argument(
        "--mask-with",
        metavar="STRING",
        default="***",
        dest="mask_string",
        help="Replacement string used for masked matches (default: ***).",
    )


def masker_from_args(args: argparse.Namespace) -> MaskerConfig:
    """Build a :class:`MaskerConfig` from parsed CLI *args*."""
    patterns: List[str] = args.mask_patterns or []
    if not patterns:
        return MaskerConfig(enabled=False)
    rules = [MaskRule(pattern=p, mask=args.mask_string) for p in patterns]
    return MaskerConfig(enabled=True, rules=rules)
