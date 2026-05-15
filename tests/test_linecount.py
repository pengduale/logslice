"""Tests for logslice.linecount."""

import pytest
from logslice.linecount import LineCountConfig, LineCountResult, LogLineCounter


def make_counter(**kwargs) -> LogLineCounter:
    return LogLineCounter(LineCountConfig(**kwargs))


# --- config validation ---

def test_invalid_max_lines_raises():
    with pytest.raises(ValueError, match="max_lines"):
        LineCountConfig(enabled=True, max_lines=0)


def test_negative_offset_raises():
    with pytest.raises(ValueError, match="offset"):
        LineCountConfig(enabled=True, offset=-1)


# --- disabled mode ---

def test_disabled_passes_all_lines():
    counter = make_counter()
    results = [counter.process(f"line {i}") for i in range(5)]
    assert all(r is not None and not r.stopped for r in results)


def test_disabled_increments_line_numbers():
    counter = make_counter()
    results = [counter.process(f"line {i}") for i in range(3)]
    assert [r.line_number for r in results] == [1, 2, 3]


def test_disabled_total_seen_and_emitted():
    counter = make_counter()
    for _ in range(4):
        counter.process("x")
    assert counter.total_seen == 4
    assert counter.total_emitted == 4


# --- offset ---

def test_offset_skips_first_n_lines():
    counter = make_counter(enabled=True, offset=2)
    results = [counter.process(f"line {i}") for i in range(5)]
    assert results[0] is None
    assert results[1] is None
    assert results[2] is not None
    assert results[2].line == "line 2"


def test_offset_line_numbers_are_absolute():
    counter = make_counter(enabled=True, offset=1)
    results = [counter.process(f"line {i}") for i in range(3)]
    visible = [r for r in results if r is not None]
    assert visible[0].line_number == 2
    assert visible[1].line_number == 3


# --- max_lines ---

def test_max_lines_stops_after_limit():
    counter = make_counter(enabled=True, max_lines=3)
    results = [counter.process(f"line {i}") for i in range(5)]
    assert results[0] is not None and not results[0].stopped
    assert results[1] is not None and not results[1].stopped
    assert results[2] is not None and not results[2].stopped
    assert results[3] is not None and results[3].stopped
    assert results[4] is not None and results[4].stopped


def test_max_lines_emitted_count_capped():
    counter = make_counter(enabled=True, max_lines=2)
    for _ in range(5):
        counter.process("x")
    assert counter.total_emitted == 2


# --- offset + max_lines ---

def test_offset_and_max_lines_combined():
    counter = make_counter(enabled=True, offset=2, max_lines=2)
    results = [counter.process(f"line {i}") for i in range(6)]
    assert results[0] is None
    assert results[1] is None
    assert results[2] is not None and not results[2].stopped
    assert results[3] is not None and not results[3].stopped
    assert results[4] is not None and results[4].stopped


# --- reset ---

def test_reset_clears_counters():
    counter = make_counter(enabled=True, max_lines=2)
    for _ in range(3):
        counter.process("x")
    counter.reset()
    assert counter.total_seen == 0
    assert counter.total_emitted == 0


def test_reset_allows_reuse():
    counter = make_counter(enabled=True, max_lines=2)
    for _ in range(3):
        counter.process("x")
    counter.reset()
    results = [counter.process(f"line {i}") for i in range(2)]
    assert all(r is not None and not r.stopped for r in results)
