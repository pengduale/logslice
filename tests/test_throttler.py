"""Tests for logslice.throttler."""

import time
from unittest.mock import patch

import pytest

from logslice.throttler import LogThrottler, ThrottlerConfig


def make_throttler(
    enabled: bool = True,
    window_seconds: float = 5.0,
    max_repeats: int = 1,
) -> LogThrottler:
    return LogThrottler(ThrottlerConfig(enabled=enabled, window_seconds=window_seconds, max_repeats=max_repeats))


def test_invalid_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        ThrottlerConfig(enabled=True, window_seconds=0)


def test_invalid_max_repeats_raises():
    with pytest.raises(ValueError, match="max_repeats"):
        ThrottlerConfig(enabled=True, max_repeats=0)


def test_disabled_passes_all_lines_including_repeats():
    t = make_throttler(enabled=False)
    assert t.process("hello") == "hello"
    assert t.process("hello") == "hello"
    assert t.process("hello") == "hello"


def test_first_occurrence_always_passes():
    t = make_throttler()
    assert t.process("unique line") == "unique line"


def test_second_occurrence_throttled_when_max_repeats_is_1():
    t = make_throttler(max_repeats=1)
    assert t.process("line") == "line"
    assert t.process("line") is None


def test_max_repeats_2_allows_two_occurrences():
    t = make_throttler(max_repeats=2)
    assert t.process("line") == "line"
    assert t.process("line") == "line"
    assert t.process("line") is None


def test_different_lines_are_tracked_independently():
    t = make_throttler(max_repeats=1)
    assert t.process("alpha") == "alpha"
    assert t.process("beta") == "beta"
    assert t.process("alpha") is None
    assert t.process("beta") is None


def test_line_passes_again_after_window_expires():
    t = make_throttler(window_seconds=1.0, max_repeats=1)
    start = time.monotonic()

    with patch("logslice.throttler.time.monotonic", return_value=start):
        assert t.process("msg") == "msg"
        assert t.process("msg") is None

    with patch("logslice.throttler.time.monotonic", return_value=start + 2.0):
        assert t.process("msg") == "msg"


def test_reset_clears_state():
    t = make_throttler(max_repeats=1)
    t.process("line")
    t.process("line")  # throttled
    assert t.tracked_count == 1
    t.reset()
    assert t.tracked_count == 0
    assert t.process("line") == "line"


def test_tracked_count_reflects_distinct_lines():
    t = make_throttler()
    t.process("a")
    t.process("b")
    t.process("a")  # duplicate, still tracked
    assert t.tracked_count == 2
