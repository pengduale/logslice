"""Tests for logslice.highlighter module."""

import pytest
from logslice.highlighter import Color, HighlightConfig, LogHighlighter


def make_highlighter(**kwargs) -> LogHighlighter:
    config = HighlightConfig(**kwargs)
    return LogHighlighter(config)


def test_disabled_returns_line_unchanged():
    h = make_highlighter(enabled=False)
    line = "ERROR something went wrong"
    assert h.highlight_line(line, pattern="ERROR") == line


def test_no_pattern_returns_line_unchanged():
    h = make_highlighter()
    line = "INFO starting up"
    result = h.highlight_line(line, pattern=None)
    assert h.strip_colors(result) == line


def test_match_is_wrapped_with_color_codes():
    h = make_highlighter(bold_matches=False, match_color=Color.RED)
    line = "ERROR disk full"
    result = h.highlight_line(line, pattern="ERROR")
    assert Color.RED in result
    assert Color.RESET in result
    assert "ERROR" in result


def test_bold_match_includes_bold_code():
    h = make_highlighter(bold_matches=True, match_color=Color.CYAN)
    line = "WARN low memory"
    result = h.highlight_line(line, pattern="WARN")
    assert Color.BOLD in result
    assert Color.CYAN in result


def test_line_color_wraps_entire_line():
    h = make_highlighter(line_color=Color.GREEN)
    line = "INFO all good"
    result = h.highlight_line(line)
    assert result.startswith(str(Color.GREEN))
    assert result.endswith(str(Color.RESET))


def test_strip_colors_removes_all_ansi_codes():
    h = make_highlighter()
    line = "WARN something"
    colored = h.highlight_line(line, pattern="WARN")
    assert h.strip_colors(colored) == line


def test_invalid_pattern_returns_line_unchanged():
    h = make_highlighter()
    line = "DEBUG [test]"
    result = h.highlight_line(line, pattern="[invalid")
    assert result == line


def test_multiple_matches_all_highlighted():
    h = make_highlighter(bold_matches=False, match_color=Color.MAGENTA)
    line = "ERROR ERROR two errors"
    result = h.highlight_line(line, pattern="ERROR")
    stripped = h.strip_colors(result)
    assert stripped == line
    assert result.count(str(Color.MAGENTA)) == 2
