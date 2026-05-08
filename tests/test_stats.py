"""Tests for logslice.stats module."""
import time
import pytest
from logslice.stats import FilterStats


def make_stats() -> FilterStats:
    return FilterStats()


def test_initial_state_is_zero():
    stats = make_stats()
    assert stats.total_lines == 0
    assert stats.matched_lines == 0
    assert stats.excluded_lines == 0
    assert stats.pattern_hit_counts == {}


def test_record_matched_line_increments_counters():
    stats = make_stats()
    stats.record_line(matched=True, pattern="ERROR")
    assert stats.total_lines == 1
    assert stats.matched_lines == 1
    assert stats.excluded_lines == 0
    assert stats.pattern_hit_counts["ERROR"] == 1


def test_record_excluded_line_increments_excluded():
    stats = make_stats()
    stats.record_line(matched=False, excluded=True)
    assert stats.total_lines == 1
    assert stats.excluded_lines == 1
    assert stats.matched_lines == 0


def test_record_unmatched_line_only_increments_total():
    stats = make_stats()
    stats.record_line(matched=False)
    assert stats.total_lines == 1
    assert stats.matched_lines == 0
    assert stats.excluded_lines == 0


def test_pattern_hit_counts_accumulate():
    stats = make_stats()
    stats.record_line(matched=True, pattern="ERROR")
    stats.record_line(matched=True, pattern="ERROR")
    stats.record_line(matched=True, pattern="WARN")
    assert stats.pattern_hit_counts["ERROR"] == 2
    assert stats.pattern_hit_counts["WARN"] == 1


def test_match_rate_is_zero_when_no_lines():
    stats = make_stats()
    assert stats.match_rate == 0.0


def test_match_rate_calculation():
    stats = make_stats()
    for _ in range(3):
        stats.record_line(matched=True)
    stats.record_line(matched=False)
    assert stats.match_rate == 0.75


def test_finish_sets_end_time():
    stats = make_stats()
    assert stats.end_time is None
    stats.finish()
    assert stats.end_time is not None


def test_elapsed_seconds_is_positive():
    stats = make_stats()
    time.sleep(0.01)
    stats.finish()
    assert stats.elapsed_seconds > 0


def test_to_dict_contains_expected_keys():
    stats = make_stats()
    stats.record_line(matched=True, pattern="DEBUG")
    stats.finish()
    d = stats.to_dict()
    assert "total_lines" in d
    assert "matched_lines" in d
    assert "excluded_lines" in d
    assert "elapsed_seconds" in d
    assert "match_rate" in d
    assert "pattern_hit_counts" in d
    assert d["pattern_hit_counts"]["DEBUG"] == 1


def test_summary_returns_string():
    stats = make_stats()
    stats.record_line(matched=True)
    stats.record_line(matched=False)
    stats.finish()
    summary = stats.summary()
    assert "2 total" in summary
    assert "1 matched" in summary
    assert "0 excluded" in summary
