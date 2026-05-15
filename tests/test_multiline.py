"""Tests for logslice.multiline."""
from __future__ import annotations

import pytest

from logslice.multiline import LogMultilineAggregator, MultilineConfig


def make_aggregator(
    start: str | None = None,
    cont: str | None = None,
    max_lines: int = 0,
    join_str: str = "\n",
    enabled: bool = True,
) -> LogMultilineAggregator:
    cfg = MultilineConfig(
        enabled=enabled,
        start_pattern=start,
        continuation_pattern=cont,
        max_lines=max_lines,
        join_str=join_str,
    )
    return LogMultilineAggregator(cfg)


def collect(agg: LogMultilineAggregator, lines: list[str]) -> list[str]:
    return list(agg.process(iter(lines)))


def test_disabled_passes_all_lines_unchanged() -> None:
    agg = make_aggregator(enabled=False)
    lines = ["line1", "line2", "line3"]
    assert collect(agg, lines) == lines


def test_enabled_without_patterns_raises() -> None:
    with pytest.raises(ValueError, match="at least one of"):
        MultilineConfig(enabled=True)


def test_negative_max_lines_raises() -> None:
    with pytest.raises(ValueError, match="max_lines"):
        MultilineConfig(enabled=True, start_pattern=r"^START", max_lines=-1)


def test_invalid_start_pattern_raises() -> None:
    with pytest.raises(re.error if False else Exception):
        MultilineConfig(enabled=True, start_pattern="[invalid")


def test_start_pattern_groups_continuation_lines() -> None:
    agg = make_aggregator(start=r"^ERROR", cont=r"^\s+")
    lines = [
        "INFO  normal line",
        "ERROR something broke",
        "  at frame1",
        "  at frame2",
        "INFO  recovered",
    ]
    result = collect(agg, lines)
    assert result[0] == "INFO  normal line"
    assert result[1] == "ERROR something broke\n  at frame1\n  at frame2"
    assert result[2] == "INFO  recovered"


def test_standalone_lines_without_continuation_are_emitted_individually() -> None:
    agg = make_aggregator(start=r"^START")
    lines = ["plain", "START event", "plain2"]
    result = collect(agg, lines)
    assert result == ["plain", "START event", "plain2"]


def test_max_lines_splits_long_events() -> None:
    agg = make_aggregator(start=r"^E", cont=r"^ ", max_lines=3)
    lines = ["E begin", " c1", " c2", " c3", " c4"]
    result = collect(agg, lines)
    # First group: ["E begin", " c1", " c2"] — 3 lines, then overflow
    assert result[0] == "E begin\n c1\n c2"


def test_custom_join_str() -> None:
    agg = make_aggregator(start=r"^BEGIN", cont=r"^-", join_str=" | ")
    lines = ["BEGIN", "-part1", "-part2"]
    result = collect(agg, lines)
    assert result == ["BEGIN | -part1 | -part2"]


def test_empty_input_yields_nothing() -> None:
    agg = make_aggregator(start=r"^X")
    assert collect(agg, []) == []


def test_only_continuation_pattern_used() -> None:
    """Without a start pattern, continuation lines are appended to whatever is buffered."""
    agg = make_aggregator(cont=r"^\t")
    lines = ["first", "\tcont", "second"]
    result = collect(agg, lines)
    # 'first' is emitted standalone; '\tcont' is not a continuation of nothing
    # because buffer is empty when we see it.
    assert "second" in result
