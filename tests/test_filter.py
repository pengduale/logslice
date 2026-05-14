"""Tests for logslice.filter module."""

import pytest
from logslice.filter import FilterConfig, LogFilter, LogMatch


SAMPLE_LINES = [
    "2024-01-01 INFO  Service started\n",
    "2024-01-01 DEBUG Connecting to database\n",
    "2024-01-01 ERROR Failed to connect: timeout\n",
    "2024-01-01 INFO  Retrying connection\n",
    "2024-01-01 ERROR Disk space low\n",
    "2024-01-01 INFO  Service stopped\n",
]


def make_filter(patterns=None, exclude_patterns=None, case_sensitive=False, max_lines=None):
    config = FilterConfig(
        patterns=patterns or [],
        exclude_patterns=exclude_patterns or [],
        case_sensitive=case_sensitive,
        max_lines=max_lines,
    )
    return LogFilter(config)


def test_no_patterns_returns_all_lines():
    lf = make_filter()
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert len(results) == len(SAMPLE_LINES)


def test_include_pattern_filters_correctly():
    lf = make_filter(patterns=[r"ERROR"])
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert len(results) == 2
    assert all("ERROR" in r.content for r in results)


def test_exclude_pattern_removes_lines():
    lf = make_filter(exclude_patterns=[r"DEBUG"])
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert all("DEBUG" not in r.content for r in results)
    assert len(results) == len(SAMPLE_LINES) - 1


def test_include_and_exclude_combined():
    lf = make_filter(patterns=[r"ERROR"], exclude_patterns=[r"Disk"])
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert len(results) == 1
    assert "timeout" in results[0].content


def test_case_insensitive_by_default():
    lf = make_filter(patterns=[r"error"])
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert len(results) == 2


def test_case_sensitive_mode():
    lf = make_filter(patterns=[r"error"], case_sensitive=True)
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert len(results) == 0


def test_max_lines_limit():
    lf = make_filter(max_lines=2)
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert len(results) == 2


def test_max_lines_with_pattern():
    """max_lines should cap results even when a pattern matches more lines."""
    lf = make_filter(patterns=[r"INFO"], max_lines=2)
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert len(results) == 2
    assert all("INFO" in r.content for r in results)


def test_log_match_line_numbers():
    lf = make_filter(patterns=[r"ERROR"])
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    assert results[0].line_number == 3
    assert results[1].line_number == 5


def test_log_match_to_dict():
    match = LogMatch(line_number=1, content="INFO hello", matched_pattern=r"INFO")
    d = match.to_dict()
    assert d["line_number"] == 1
    assert d["content"] == "INFO hello"
    assert d["matched_pattern"] == r"INFO"


def test_matched_pattern_recorded():
    lf = make_filter(patterns=[r"ERROR", r"INFO"])
    results = list(lf.filter_lines(iter(SAMPLE_LINES)))
    error_matches = [r for r in results if "ERROR" in r.content]
    assert all(r.matched_pattern == "ERROR" for r in error_matches)
