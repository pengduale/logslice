"""Tests for logslice.fieldextractor_cli."""
import argparse

import pytest

from logslice.fieldextractor_cli import add_fieldextractor_args, fieldextractor_from_args


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_fieldextractor_args(p)
    return p


def parse(argv) -> argparse.Namespace:
    return build_parser().parse_args(argv)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_no_args_produces_disabled_config():
    cfg = fieldextractor_from_args(parse([]))
    assert cfg.enabled is False
    assert cfg.patterns == []


def test_single_extract_pattern_enables_extractor():
    cfg = fieldextractor_from_args(parse(["--extract", r"(?P<level>\w+)"]))
    assert cfg.enabled is True
    assert len(cfg.patterns) == 1


def test_multiple_extract_patterns_are_collected():
    cfg = fieldextractor_from_args(
        parse([
            "--extract", r"(?P<level>\w+)",
            "--extract", r"(?P<code>\d{3})",
        ])
    )
    assert cfg.enabled is True
    assert len(cfg.patterns) == 2


def test_extract_all_flag_is_parsed():
    ns = parse(["--extract", r"(?P<level>\w+)", "--extract-all"])
    assert ns.extract_all is True


def test_extract_all_defaults_to_false():
    ns = parse(["--extract", r"(?P<level>\w+)"])
    assert ns.extract_all is False


def test_invalid_pattern_raises_on_config_build():
    ns = parse(["--extract", r"(unclosed"])
    with pytest.raises(ValueError, match="Invalid pattern"):
        fieldextractor_from_args(ns)


def test_pattern_without_named_groups_raises_on_config_build():
    ns = parse(["--extract", r"(\d+)"])
    with pytest.raises(ValueError, match="no named groups"):
        fieldextractor_from_args(ns)
