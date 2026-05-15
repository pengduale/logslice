"""CLI helpers for the time-window filter."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Optional

from logslice.timewindow import TimeWindowConfig

_ISO_FMTS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
]


def _parse_dt(value: str) -> datetime:
    for fmt in _ISO_FMTS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime {value!r}. "
        "Expected ISO-8601 format, e.g. 2024-01-15T08:30:00"
    )


def add_timewindow_args(parser: argparse.ArgumentParser) -> None:
    """Attach --time-start / --time-end / --time-drop-unparsed to *parser*."""
    grp = parser.add_argument_group("time-window filtering")
    grp.add_argument(
        "--time-start",
        metavar="DATETIME",
        type=_parse_dt,
        default=None,
        help="Discard lines whose timestamp is before DATETIME (ISO-8601).",
    )
    grp.add_argument(
        "--time-end",
        metavar="DATETIME",
        type=_parse_dt,
        default=None,
        help="Discard lines whose timestamp is after DATETIME (ISO-8601).",
    )
    grp.add_argument(
        "--time-drop-unparsed",
        action="store_true",
        default=False,
        help="Drop lines that contain no recognisable timestamp (default: keep).",
    )


def timewindow_from_args(args: argparse.Namespace) -> TimeWindowConfig:
    """Build a :class:`TimeWindowConfig` from parsed CLI *args*."""
    start: Optional[datetime] = getattr(args, "time_start", None)
    end: Optional[datetime] = getattr(args, "time_end", None)
    drop: bool = getattr(args, "time_drop_unparsed", False)
    enabled = start is not None or end is not None
    return TimeWindowConfig(enabled=enabled, start=start, end=end, drop_unparsed=drop)
