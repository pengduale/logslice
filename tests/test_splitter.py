"""Tests for logslice.splitter."""
import pytest

from logslice.splitter import LogSplitter, SplitterConfig


def make_splitter(**kwargs) -> LogSplitter:
    return LogSplitter(SplitterConfig(**kwargs))


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_disabled_requires_no_delimiter_or_regex():
    cfg = SplitterConfig(enabled=False)
    assert cfg.delimiter is None and cfg.regex is None


def test_enabled_without_delimiter_or_regex_raises():
    with pytest.raises(ValueError, match="requires either"):
        SplitterConfig(enabled=True)


def test_enabled_with_both_delimiter_and_regex_raises():
    with pytest.raises(ValueError, match="not both"):
        SplitterConfig(enabled=True, delimiter="|", regex=r"(\w+)")


def test_invalid_regex_raises():
    with pytest.raises(ValueError, match="Invalid splitter regex"):
        SplitterConfig(enabled=True, regex=r"(unclosed")


# ---------------------------------------------------------------------------
# Disabled behaviour
# ---------------------------------------------------------------------------

def test_disabled_returns_none():
    s = make_splitter(enabled=False)
    assert s.split("hello world") is None


# ---------------------------------------------------------------------------
# Delimiter splitting
# ---------------------------------------------------------------------------

def test_delimiter_splits_into_positional_keys():
    s = make_splitter(enabled=True, delimiter="|", include_raw=False)
    result = s.split("a|b|c")
    assert result == {"field_0": "a", "field_1": "b", "field_2": "c"}


def test_delimiter_uses_field_names():
    s = make_splitter(
        enabled=True, delimiter=",",
        field_names=["level", "msg"],
        include_raw=False,
    )
    result = s.split("ERROR,disk full")
    assert result == {"level": "ERROR", "msg": "disk full"}


def test_delimiter_extra_parts_get_positional_keys():
    s = make_splitter(
        enabled=True, delimiter=",",
        field_names=["level"],
        include_raw=False,
    )
    result = s.split("ERROR,disk full,host1")
    assert result["level"] == "ERROR"
    assert result["field_1"] == "disk full"
    assert result["field_2"] == "host1"


def test_include_raw_adds_raw_key():
    s = make_splitter(enabled=True, delimiter="|", include_raw=True)
    line = "x|y"
    result = s.split(line)
    assert result is not None
    assert result["_raw"] == line


# ---------------------------------------------------------------------------
# Regex splitting
# ---------------------------------------------------------------------------

def test_regex_captures_named_positional_fields():
    s = make_splitter(
        enabled=True,
        regex=r"(\w+)\s+(\d+)",
        field_names=["word", "number"],
        include_raw=False,
    )
    result = s.split("hello 42")
    assert result == {"word": "hello", "number": "42"}


def test_regex_no_match_returns_empty_dict_with_raw():
    s = make_splitter(enabled=True, regex=r"(\d+)", include_raw=True)
    result = s.split("no digits here")
    assert result is not None
    assert "_raw" in result
    assert len(result) == 1  # only _raw


def test_regex_no_groups_uses_full_match():
    s = make_splitter(enabled=True, regex=r"ERROR", include_raw=False)
    result = s.split("ERROR occurred")
    assert result == {"field_0": "ERROR"}
