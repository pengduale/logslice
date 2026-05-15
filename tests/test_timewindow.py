"""Tests for logslice.timewindow and logslice.timewindow_cli."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

import pytest

from logslice.timewindow import LogTimeWindow, TimeWindowConfig
from logslice.timewindow_cli import add_timewindow_args, timewindow_from_args


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def make_window(**kwargs) -> LogTimeWindow:
    return LogTimeWindow(TimeWindowConfig(**kwargs))


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_enabled_without_start_or_end_raises():
    with pytest.raises(ValueError, match="at least one"):
        TimeWindowConfig(enabled=True)


def test_start_after_end_raises():
    with pytest.raises(ValueError, match="start must not be after end"):
        TimeWindowConfig(enabled=True, start=_dt("2024-06-01T12:00:00"), end=_dt("2024-01-01T00:00:00"))


# ---------------------------------------------------------------------------
# Disabled passthrough
# ---------------------------------------------------------------------------

def test_disabled_passes_all_lines():
    w = make_window()
    assert w.process("no timestamp here").passed is True
    assert w.process("2024-01-01T00:00:00 something").passed is True


# ---------------------------------------------------------------------------
# Timestamp parsing & window logic
# ---------------------------------------------------------------------------

def test_line_inside_window_passes():
    w = make_window(enabled=True, start=_dt("2024-03-01T00:00:00"), end=_dt("2024-03-31T23:59:59"))
    result = w.process("2024-03-15T10:30:00 INFO service started")
    assert result.passed is True
    assert result.reason == "in_window"


def test_line_before_start_is_dropped():
    w = make_window(enabled=True, start=_dt("2024-03-01T00:00:00"))
    result = w.process("2024-02-28T23:59:59 INFO old event")
    assert result.passed is False
    assert result.reason == "before_start"


def test_line_after_end_is_dropped():
    w = make_window(enabled=True, end=_dt("2024-03-31T23:59:59"))
    result = w.process("2024-04-01T00:00:01 INFO future event")
    assert result.passed is False
    assert result.reason == "after_end"


def test_no_timestamp_kept_by_default():
    w = make_window(enabled=True, start=_dt("2024-01-01T00:00:00"))
    result = w.process("plain log line without any timestamp")
    assert result.passed is True
    assert result.reason == "no_timestamp"


def test_no_timestamp_dropped_when_configured():
    w = make_window(enabled=True, start=_dt("2024-01-01T00:00:00"), drop_unparsed=True)
    result = w.process("plain log line without any timestamp")
    assert result.passed is False


def test_space_separated_timestamp_parsed():
    w = make_window(enabled=True, start=_dt("2024-01-01T00:00:00"))
    result = w.process("2024-05-20 14:22:33 DEBUG something happened")
    assert result.passed is True
    assert result.timestamp is not None


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_timewindow_args(p)
    return p


def parse(args: list[str]) -> argparse.Namespace:
    return _build_parser().parse_args(args)


def test_no_args_produces_disabled_config():
    cfg = timewindow_from_args(parse([]))
    assert cfg.enabled is False


def test_time_start_enables_filter():
    cfg = timewindow_from_args(parse(["--time-start", "2024-03-01T00:00:00"]))
    assert cfg.enabled is True
    assert cfg.start == _dt("2024-03-01T00:00:00")
    assert cfg.end is None


def test_time_end_enables_filter():
    cfg = timewindow_from_args(parse(["--time-end", "2024-03-31"]))
    assert cfg.enabled is True
    assert cfg.end is not None


def test_both_bounds_set_correctly():
    cfg = timewindow_from_args(parse([
        "--time-start", "2024-01-01",
        "--time-end", "2024-12-31",
    ]))
    assert cfg.start < cfg.end  # type: ignore[operator]


def test_drop_unparsed_flag():
    cfg = timewindow_from_args(parse(["--time-start", "2024-01-01", "--time-drop-unparsed"]))
    assert cfg.drop_unparsed is True
