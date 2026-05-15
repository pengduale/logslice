"""CLI helpers for configuring the LogThrottler from parsed arguments."""

from __future__ import annotations

import argparse
from typing import Optional

from logslice.throttler import LogThrottler, ThrottlerConfig


def add_throttler_args(parser: argparse.ArgumentParser) -> None:
    """Register throttler-related CLI flags on *parser*."""
    grp = parser.add_argument_group("throttling")
    grp.add_argument(
        "--throttle",
        action="store_true",
        default=False,
        help="Suppress repeated identical lines within a time window.",
    )
    grp.add_argument(
        "--throttle-window",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="Duration of the throttle window in seconds (default: 5.0).",
    )
    grp.add_argument(
        "--throttle-max-repeats",
        type=int,
        default=1,
        metavar="N",
        help="Max times a line may appear within the window before being suppressed (default: 1).",
    )


def throttler_from_args(args: argparse.Namespace) -> Optional[LogThrottler]:
    """Build a :class:`LogThrottler` from parsed CLI *args*, or return None.

    Returns None when throttling is disabled so callers can skip the step
    entirely without special-casing.
    """
    if not args.throttle:
        return None

    try:
        config = ThrottlerConfig(
            enabled=True,
            window_seconds=args.throttle_window,
            max_repeats=args.throttle_max_repeats,
        )
    except ValueError as exc:
        raise SystemExit(f"throttler: {exc}") from exc

    return LogThrottler(config)
