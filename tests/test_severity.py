"""Tests for logslice.severity."""

import re
import pytest

from logslice.severity import Level, LogSeverityFilter, SeverityConfig


def make_filter(
    enabled: bool = True,
    min_level: Level = Level.DEBUG,
    max_level: Level = Level.CRITICAL,
) -> LogSeverityFilter:
    return LogSeverityFilter(SeverityConfig(enabled=enabled, min_level=min_level, max_level=max_level))


def test_level_parse_case_insensitive():
    assert Level.parse("debug") == Level.DEBUG
    assert Level.parse("WARNING") == Level.WARNING


def test_level_parse_unknown_raises():
    with pytest.raises(ValueError, match="Unknown log level"):
        Level.parse("VERBOSE")


def test_min_greater_than_max_raises():
    with pytest.raises(ValueError, match="min_level"):
        SeverityConfig(enabled=True, min_level=Level.ERROR, max_level=Level.DEBUG)


def test_disabled_passes_all_lines():
    f = make_filter(enabled=False)
    assert f.process("DEBUG something") == "DEBUG something"
    assert f.process("no level here") == "no level here"


def test_detect_level_debug():
    f = make_filter()
    assert f.detect_level("2024-01-01 DEBUG starting up") == Level.DEBUG


def test_detect_level_warn_alias():
    f = make_filter()
    assert f.detect_level("[WARN] disk space low") == Level.WARNING


def test_detect_level_fatal_alias():
    f = make_filter()
    assert f.detect_level("FATAL unrecoverable error") == Level.CRITICAL


def test_detect_level_returns_none_when_no_match():
    f = make_filter()
    assert f.detect_level("nothing interesting here") is None


def test_min_level_filters_below():
    f = make_filter(min_level=Level.WARNING)
    assert f.process("DEBUG verbose output") is None
    assert f.process("INFO informational") is None
    assert f.process("WARNING watch out") == "WARNING watch out"


def test_max_level_filters_above():
    f = make_filter(max_level=Level.WARNING)
    assert f.process("ERROR something failed") is None
    assert f.process("CRITICAL total failure") is None
    assert f.process("WARNING last allowed") == "WARNING last allowed"


def test_exact_level_range():
    f = make_filter(min_level=Level.INFO, max_level=Level.ERROR)
    assert f.process("DEBUG too low") is None
    assert f.process("INFO just right") == "INFO just right"
    assert f.process("ERROR also fine") == "ERROR also fine"
    assert f.process("CRITICAL too high") is None


def test_no_level_in_line_passes_through():
    f = make_filter(min_level=Level.ERROR)
    assert f.process("plain log line without level") == "plain log line without level"


def test_custom_pattern_is_used():
    custom = re.compile(r"\[(HIGH|LOW)\]", re.IGNORECASE)
    # custom tokens won't map to Level — treated as unknown → pass through
    cfg = SeverityConfig(enabled=True, min_level=Level.ERROR, pattern=custom)
    f = LogSeverityFilter(cfg)
    # pattern matches but token is unrecognised → passes through
    assert f.process("[LOW] some message") == "[LOW] some message"
