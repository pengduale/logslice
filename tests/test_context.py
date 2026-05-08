"""Tests for logslice.context module."""
import pytest
from logslice.context import ContextConfig, ContextCollector
from logslice.filter import LogMatch


def make_match(line: str, line_number: int, source: str = "test.log") -> LogMatch:
    return LogMatch(line=line, line_number=line_number, source=source, matched_patterns=["pat"])


def collect(collector: ContextCollector, lines, matches: set):
    results = []
    for i, text in enumerate(lines, start=1):
        m = make_match(text, i) if i in matches else None
        results.extend(collector.feed(m, text, i))
    return results


def test_invalid_before_raises():
    with pytest.raises(ValueError):
        ContextConfig(before=-1)


def test_invalid_after_raises():
    with pytest.raises(ValueError):
        ContextConfig(after=-1)


def test_disabled_when_both_zero():
    cfg = ContextConfig(before=0, after=0)
    assert not cfg.enabled


def test_enabled_when_before_set():
    assert ContextConfig(before=2).enabled


def test_enabled_when_after_set():
    assert ContextConfig(after=1).enabled


def test_no_context_returns_only_match():
    cfg = ContextConfig(before=0, after=0)
    collector = ContextCollector(cfg)
    lines = ["a", "b", "c"]
    results = collect(collector, lines, matches={2})
    assert len(results) == 1
    assert results[0].line == "b"
    assert results[0].context_tag is None


def test_before_context_includes_preceding_lines():
    cfg = ContextConfig(before=2, after=0)
    collector = ContextCollector(cfg)
    lines = ["line1", "line2", "line3", "MATCH", "line5"]
    results = collect(collector, lines, matches={4})
    result_lines = [r.line for r in results]
    assert "line2" in result_lines
    assert "line3" in result_lines
    assert "MATCH" in result_lines
    assert "line1" not in result_lines
    assert "line5" not in result_lines


def test_after_context_includes_following_lines():
    cfg = ContextConfig(before=0, after=2)
    collector = ContextCollector(cfg)
    lines = ["line1", "MATCH", "line3", "line4", "line5"]
    results = collect(collector, lines, matches={2})
    result_lines = [r.line for r in results]
    assert "MATCH" in result_lines
    assert "line3" in result_lines
    assert "line4" in result_lines
    assert "line5" not in result_lines


def test_context_tag_before_is_set():
    cfg = ContextConfig(before=1, after=0)
    collector = ContextCollector(cfg)
    lines = ["prev", "MATCH"]
    results = collect(collector, lines, matches={2})
    before_results = [r for r in results if r.context_tag == "before"]
    assert len(before_results) == 1
    assert before_results[0].line == "prev"


def test_context_tag_after_is_set():
    cfg = ContextConfig(before=0, after=1)
    collector = ContextCollector(cfg)
    lines = ["MATCH", "after_line"]
    results = collect(collector, lines, matches={1})
    after_results = [r for r in results if r.context_tag == "after"]
    assert len(after_results) == 1
    assert after_results[0].line == "after_line"


def test_no_duplicate_lines_when_matches_are_adjacent():
    cfg = ContextConfig(before=1, after=1)
    collector = ContextCollector(cfg)
    lines = ["a", "MATCH1", "MATCH2", "d"]
    results = collect(collector, lines, matches={2, 3})
    seen_numbers = [r.line_number for r in results]
    assert len(seen_numbers) == len(set(seen_numbers)), "Duplicate line numbers found"
