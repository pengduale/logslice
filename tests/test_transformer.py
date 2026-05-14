"""Tests for logslice.transformer."""

import pytest

from logslice.transformer import LogTransformer, TransformerConfig, TransformRule


def make_transformer(*rules: TransformRule, enabled: bool = True) -> LogTransformer:
    cfg = TransformerConfig(enabled=enabled, rules=list(rules))
    return LogTransformer(cfg)


def test_invalid_pattern_raises() -> None:
    with pytest.raises(ValueError, match="Invalid transform pattern"):
        TransformRule(pattern="[invalid", replacement="x")


def test_disabled_returns_line_unchanged() -> None:
    rule = TransformRule(pattern=r"\d+", replacement="NUM")
    transformer = make_transformer(rule, enabled=False)
    assert transformer.process("error on line 42") == "error on line 42"


def test_no_rules_returns_line_unchanged() -> None:
    transformer = make_transformer()
    assert transformer.process("hello world") == "hello world"


def test_single_rule_replaces_match() -> None:
    rule = TransformRule(pattern=r"\d+", replacement="NUM")
    transformer = make_transformer(rule)
    assert transformer.process("error on line 42") == "error on line NUM"


def test_single_rule_no_match_returns_original() -> None:
    rule = TransformRule(pattern=r"\d+", replacement="NUM")
    transformer = make_transformer(rule)
    assert transformer.process("no digits here") == "no digits here"


def test_multiple_rules_applied_in_order() -> None:
    rule1 = TransformRule(pattern=r"foo", replacement="bar")
    rule2 = TransformRule(pattern=r"bar", replacement="baz")
    transformer = make_transformer(rule1, rule2)
    # foo -> bar -> baz
    assert transformer.process("foo") == "baz"


def test_rule_replaces_all_occurrences() -> None:
    rule = TransformRule(pattern=r"x", replacement="y")
    transformer = make_transformer(rule)
    assert transformer.process("x and x and x") == "y and y and y"


def test_rule_with_group_reference() -> None:
    rule = TransformRule(pattern=r"(\w+)@(\w+)\.com", replacement=r"[\1 at \2]")
    transformer = make_transformer(rule)
    assert transformer.process("contact user@example.com today") == "contact [user at example] today"


def test_config_property_returns_config() -> None:
    cfg = TransformerConfig(enabled=True, rules=[])
    transformer = LogTransformer(cfg)
    assert transformer.config is cfg


def test_default_config_is_enabled_with_no_rules() -> None:
    transformer = LogTransformer()
    assert transformer.config.enabled is True
    assert transformer.config.rules == []
