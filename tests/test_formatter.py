"""Tests for logslice.formatter module."""

import json
import pytest
from logslice.filter import LogMatch
from logslice.formatter import LogFormatter, OutputFormat
from logslice.highlighter import Color, HighlightConfig


def make_match(
    line: str = "ERROR something failed",
    line_number: int = 42,
    source: str = "app.log",
    matched_pattern: str = "ERROR",
) -> LogMatch:
    return LogMatch(
        line=line,
        line_number=line_number,
        source=source,
        matched_pattern=matched_pattern,
    )


def test_plain_format_includes_line_number_and_source():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN)
    result = fmt.format_match(make_match())
    assert "42:" in result
    assert "[app.log]" in result
    assert "ERROR something failed" in result


def test_plain_format_hides_line_number_when_disabled():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN, show_line_numbers=False)
    result = fmt.format_match(make_match())
    assert "42:" not in result


def test_plain_format_hides_source_when_disabled():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN, show_source=False)
    result = fmt.format_match(make_match())
    assert "[app.log]" not in result


def test_json_format_returns_valid_json():
    fmt = LogFormatter(fmt=OutputFormat.JSON)
    result = fmt.format_match(make_match())
    data = json.loads(result)
    assert data["line"] == "ERROR something failed"
    assert data["line_number"] == 42
    assert data["source"] == "app.log"
    assert "timestamp" in data


def test_color_format_contains_ansi_codes():
    cfg = HighlightConfig(enabled=True, match_color=Color.RED, bold_matches=False)
    fmt = LogFormatter(fmt=OutputFormat.COLOR, highlight_config=cfg)
    result = fmt.format_match(make_match())
    assert str(Color.RED) in result
    assert str(Color.RESET) in result


def test_color_format_disabled_highlight_no_ansi():
    cfg = HighlightConfig(enabled=False)
    fmt = LogFormatter(fmt=OutputFormat.COLOR, highlight_config=cfg)
    result = fmt.format_match(make_match())
    assert "\033[" not in result


def test_format_all_returns_list_of_strings():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN)
    matches = [make_match(line_number=i) for i in range(1, 4)]
    results = fmt.format_all(matches)
    assert len(results) == 3
    assert all(isinstance(r, str) for r in results)
