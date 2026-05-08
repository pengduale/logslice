"""Tests for logslice.deduplicator."""

import pytest
from logslice.deduplicator import DeduplicatorConfig, LogDeduplicator


def make_deduplicator(**kwargs) -> LogDeduplicator:
    return LogDeduplicator(DeduplicatorConfig(**kwargs))


def test_disabled_passes_all_lines_including_duplicates():
    d = make_deduplicator(enabled=False)
    assert d.process("hello\n") == "hello\n"
    assert d.process("hello\n") == "hello\n"


def test_first_occurrence_is_always_returned():
    d = make_deduplicator(enabled=True)
    result = d.process("unique line\n")
    assert result == "unique line\n"


def test_duplicate_is_suppressed_when_show_count_false():
    d = make_deduplicator(enabled=True, show_count=False)
    d.process("dup\n")
    result = d.process("dup\n")
    assert result is None


def test_duplicate_returns_annotated_line_when_show_count_true():
    d = make_deduplicator(enabled=True, show_count=True)
    d.process("dup\n")
    result = d.process("dup\n")
    assert result == "dup [x2]\n"


def test_count_increments_on_each_duplicate():
    d = make_deduplicator(enabled=True, show_count=True)
    d.process("line\n")
    d.process("line\n")  # x2
    result = d.process("line\n")  # x3
    assert result == "line [x3]\n"


def test_different_lines_are_not_deduplicated():
    d = make_deduplicator(enabled=True)
    assert d.process("line a\n") == "line a\n"
    assert d.process("line b\n") == "line b\n"


def test_window_evicts_oldest_entry_when_full():
    d = make_deduplicator(enabled=True, window_size=3, show_count=False)
    d.process("a\n")
    d.process("b\n")
    d.process("c\n")
    # window is full; adding 'd' should evict 'a'
    d.process("d\n")
    assert d.unique_count == 3
    # 'a' was evicted so it is treated as new again
    result = d.process("a\n")
    assert result == "a\n"


def test_reset_clears_window():
    d = make_deduplicator(enabled=True, show_count=False)
    d.process("hello\n")
    d.reset()
    # After reset the same line should pass through again
    assert d.process("hello\n") == "hello\n"


def test_unique_count_reflects_window_contents():
    d = make_deduplicator(enabled=True)
    assert d.unique_count == 0
    d.process("x\n")
    d.process("y\n")
    assert d.unique_count == 2


def test_line_without_newline_is_handled():
    d = make_deduplicator(enabled=True, show_count=True)
    d.process("no newline")
    result = d.process("no newline")
    assert result == "no newline [x2]"
