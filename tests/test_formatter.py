"""Tests for logslice.formatter."""

import json

import pytest

from logslice.filter import LogMatch
from logslice.formatter import LogFormatter, OutputFormat


def make_match(line: str, line_number: int = 1, source: str = "app.log") -> LogMatch:
    return LogMatch(line=line, line_number=line_number, source=source, matched_patterns=[r".*"])


def test_plain_format_includes_line_number_and_source():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN)
    result = fmt.format_match(make_match("hello world", line_number=5))
    assert "[5]" in result
    assert "(app.log)" in result
    assert "hello world" in result


def test_plain_format_hides_line_number_when_disabled():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN, show_line_numbers=False)
    result = fmt.format_match(make_match("hello", line_number=3))
    assert "[3]" not in result
    assert "hello" in result


def test_plain_format_hides_source_when_disabled():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN, show_source=False)
    result = fmt.format_match(make_match("hello", source="server.log"))
    assert "(server.log)" not in result


def test_json_format_returns_valid_json():
    fmt = LogFormatter(fmt=OutputFormat.JSON)
    result = fmt.format_match(make_match("error occurred", line_number=10))
    data = json.loads(result)
    assert data["line"] == "error occurred"
    assert data["line_number"] == 10
    assert data["source"] == "app.log"


def test_json_format_includes_timestamp_when_enabled():
    fmt = LogFormatter(fmt=OutputFormat.JSON, timestamp=True)
    result = fmt.format_match(make_match("test"))
    data = json.loads(result)
    assert "formatted_at" in data
    assert data["formatted_at"].endswith("Z")


def test_csv_format_structure():
    fmt = LogFormatter(fmt=OutputFormat.CSV)
    result = fmt.format_match(make_match("some log line", line_number=7, source="svc.log"))
    parts = result.split(",", 2)
    assert parts[0] == "7"
    assert parts[1] == "svc.log"
    assert "some log line" in parts[2]


def test_csv_header():
    fmt = LogFormatter(fmt=OutputFormat.CSV)
    assert fmt.csv_header() == "line_number,source,line"


def test_format_matches_returns_list():
    fmt = LogFormatter(fmt=OutputFormat.PLAIN)
    matches = [make_match(f"line {i}", line_number=i) for i in range(1, 4)]
    results = fmt.format_matches(matches)
    assert len(results) == 3
    assert all(isinstance(r, str) for r in results)


def test_invalid_format_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported format"):
        LogFormatter(fmt="xml")
