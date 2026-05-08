"""Tests for logslice.truncator."""
import pytest
from logslice.truncator import TruncatorConfig, LogTruncator


def make_truncator(enabled: bool = True, max_length: int = 20, ellipsis: str = "...") -> LogTruncator:
    config = TruncatorConfig(enabled=enabled, max_length=max_length, ellipsis=ellipsis)
    return LogTruncator(config)


def test_invalid_max_length_raises():
    with pytest.raises(ValueError, match="max_length"):
        TruncatorConfig(enabled=True, max_length=0)


def test_ellipsis_too_long_raises():
    with pytest.raises(ValueError, match="ellipsis"):
        TruncatorConfig(enabled=True, max_length=3, ellipsis="...")


def test_disabled_returns_line_unchanged():
    truncator = make_truncator(enabled=False)
    long_line = "x" * 100
    assert truncator.process(long_line) == long_line


def test_short_line_returned_unchanged():
    truncator = make_truncator(max_length=20)
    line = "short line"
    assert truncator.process(line) == line


def test_line_at_exact_max_length_not_truncated():
    truncator = make_truncator(max_length=20)
    line = "a" * 20
    assert truncator.process(line) == line


def test_line_exceeding_max_length_is_truncated():
    truncator = make_truncator(max_length=20, ellipsis="...")
    line = "a" * 30
    result = truncator.process(line)
    assert len(result) == 20
    assert result.endswith("...")


def test_truncated_content_is_prefix_of_original():
    truncator = make_truncator(max_length=10, ellipsis="..")
    line = "hello world this is a long line"
    result = truncator.process(line)
    assert result == "hello wor.."


def test_custom_ellipsis_is_used():
    truncator = make_truncator(max_length=15, ellipsis="[cut]")
    line = "a" * 30
    result = truncator.process(line)
    assert result.endswith("[cut]")
    assert len(result) == 15


def test_was_truncated_returns_false_when_disabled():
    truncator = make_truncator(enabled=False, max_length=5)
    assert truncator.was_truncated("hello world") is False


def test_was_truncated_returns_false_for_short_line():
    truncator = make_truncator(max_length=20)
    assert truncator.was_truncated("short") is False


def test_was_truncated_returns_true_for_long_line():
    truncator = make_truncator(max_length=10)
    assert truncator.was_truncated("this is definitely longer than ten chars") is True


def test_default_config_is_disabled():
    truncator = LogTruncator()
    assert truncator.config.enabled is False
    long_line = "x" * 500
    assert truncator.process(long_line) == long_line
