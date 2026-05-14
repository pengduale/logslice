"""Tests for logslice.redactor."""

import pytest

from logslice.redactor import LogRedactor, RedactorConfig, RedactRule


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_redactor(*patterns_replacements, enabled: bool = True) -> LogRedactor:
    rules = [
        RedactRule(pattern=p, replacement=r)
        for p, r in patterns_replacements
    ]
    return LogRedactor(RedactorConfig(enabled=enabled, rules=rules))


# ---------------------------------------------------------------------------
# RedactRule
# ---------------------------------------------------------------------------

def test_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid redact pattern"):
        RedactRule(pattern="[unclosed")


def test_rule_replaces_match():
    rule = RedactRule(pattern=r"\d{4}", replacement="****")
    result, count = rule.apply("error code 1234 on line 5678")
    assert result == "error code **** on line ****"
    assert count == 2


def test_rule_no_match_returns_original():
    rule = RedactRule(pattern=r"SECRET")
    result, count = rule.apply("nothing sensitive here")
    assert result == "nothing sensitive here"
    assert count == 0


# ---------------------------------------------------------------------------
# LogRedactor — disabled
# ---------------------------------------------------------------------------

def test_disabled_returns_line_unchanged():
    redactor = make_redactor((r"password=\S+", "[REDACTED]"), enabled=False)
    line = "user login password=s3cr3t"
    assert redactor.process(line) == line


def test_disabled_does_not_increment_counter():
    redactor = make_redactor((r"\d+", "NUM"), enabled=False)
    redactor.process("value 42")
    assert redactor.total_redactions == 0


# ---------------------------------------------------------------------------
# LogRedactor — enabled
# ---------------------------------------------------------------------------

def test_no_rules_returns_line_unchanged():
    redactor = LogRedactor(RedactorConfig(enabled=True, rules=[]))
    assert redactor.process("some line") == "some line"


def test_single_rule_redacts_match():
    redactor = make_redactor((r"token=[A-Za-z0-9]+", "token=[REDACTED]"))
    result = redactor.process("auth token=abc123 granted")
    assert result == "auth token=[REDACTED] granted"


def test_multiple_rules_applied_in_order():
    redactor = make_redactor(
        (r"\d{3}-\d{2}-\d{4}", "[SSN]"),
        (r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", "[EMAIL]"),
    )
    line = "contact 123-45-6789 or user@example.com"
    result = redactor.process(line)
    assert "[SSN]" in result
    assert "[EMAIL]" in result
    assert "123-45-6789" not in result
    assert "user@example.com" not in result


def test_total_redactions_accumulates_across_calls():
    redactor = make_redactor((r"\d+", "NUM"))
    redactor.process("line 1 has 2 numbers")
    redactor.process("another 3 here")
    assert redactor.total_redactions == 3


def test_reset_stats_clears_counter():
    redactor = make_redactor((r"\d+", "NUM"))
    redactor.process("42 items")
    assert redactor.total_redactions == 1
    redactor.reset_stats()
    assert redactor.total_redactions == 0


def test_default_replacement_is_redacted_label():
    redactor = make_redactor((r"secret", "[REDACTED]"))
    result = redactor.process("this is secret info")
    assert result == "this is [REDACTED] info"
