"""Tests for logslice.masker and logslice.masker_cli."""
from __future__ import annotations

import argparse
import pytest

from logslice.masker import LogMasker, MaskRule, MaskerConfig
from logslice.masker_cli import add_masker_args, masker_from_args


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_masker(patterns=None, mask="***", enabled=True) -> LogMasker:
    rules = [MaskRule(pattern=p, mask=mask) for p in (patterns or [])]
    return LogMasker(MaskerConfig(enabled=enabled, rules=rules))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_masker_args(p)
    return p


def parse(argv) -> argparse.Namespace:
    return build_parser().parse_args(argv)


# ---------------------------------------------------------------------------
# MaskRule
# ---------------------------------------------------------------------------

def test_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid mask pattern"):
        MaskRule(pattern="[unclosed")


def test_rule_replaces_match():
    rule = MaskRule(pattern=r"\d+", mask="NUM")
    assert rule.apply("error on line 42") == "error on line NUM"


def test_rule_no_match_returns_original():
    rule = MaskRule(pattern=r"\d+", mask="NUM")
    assert rule.apply("no digits here") == "no digits here"


def test_rule_replaces_all_occurrences():
    rule = MaskRule(pattern=r"secret", mask="***")
    assert rule.apply("secret and secret") == "*** and ***"


# ---------------------------------------------------------------------------
# LogMasker
# ---------------------------------------------------------------------------

def test_disabled_returns_line_unchanged():
    masker = make_masker(patterns=[r"\d+"], enabled=False)
    assert masker.process("value=42") == "value=42"


def test_no_rules_returns_line_unchanged():
    masker = make_masker(patterns=[], enabled=True)
    assert masker.process("value=42") == "value=42"


def test_single_rule_masks_sensitive_data():
    masker = make_masker(patterns=[r"password=\S+"], mask="password=***")
    assert masker.process("login password=s3cr3t ok") == "login password=*** ok"


def test_multiple_rules_applied_in_order():
    masker = make_masker(patterns=[r"\d+", r"foo"], mask="X")
    result = masker.process("foo 99")
    assert result == "X X"


def test_process_many_applies_to_all_lines():
    masker = make_masker(patterns=[r"\d+"], mask="N")
    lines = ["line 1", "line 2", "no digits"]
    assert masker.process_many(lines) == ["line N", "line N", "no digits"]


# ---------------------------------------------------------------------------
# masker_cli
# ---------------------------------------------------------------------------

def test_no_args_produces_disabled_config():
    cfg = masker_from_args(parse([]))
    assert not cfg.enabled
    assert cfg.rules == []


def test_single_mask_pattern_enables_masker():
    cfg = masker_from_args(parse(["--mask", r"\d+"]))
    assert cfg.enabled
    assert len(cfg.rules) == 1


def test_multiple_mask_patterns_collected():
    cfg = masker_from_args(parse(["--mask", r"\d+", "--mask", "secret"]))
    assert len(cfg.rules) == 2


def test_custom_mask_string_propagated():
    cfg = masker_from_args(parse(["--mask", r"\d+", "--mask-with", "REDACTED"]))
    assert cfg.rules[0].mask == "REDACTED"


def test_default_mask_string_is_asterisks():
    cfg = masker_from_args(parse(["--mask", r"\d+"]))
    assert cfg.rules[0].mask == "***"
