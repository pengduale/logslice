"""Tests for logslice.linecount_cli."""

import argparse
import pytest

from logslice.linecount_cli import add_linecount_args, linecount_from_args
from logslice.linecount import LineCountConfig


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_linecount_args(p)
    return p


def parse(argv: list) -> argparse.Namespace:
    return build_parser().parse_args(argv)


# --- no args ---

def test_no_args_produces_disabled_config():
    cfg = linecount_from_args(parse([]))
    assert cfg.enabled is False
    assert cfg.max_lines is None
    assert cfg.offset == 0


# --- --head ---

def test_head_enables_config():
    cfg = linecount_from_args(parse(["--head", "10"]))
    assert cfg.enabled is True
    assert cfg.max_lines == 10


def test_head_zero_is_invalid():
    """argparse accepts the value; LineCountConfig validates it."""
    with pytest.raises(ValueError):
        linecount_from_args(parse(["--head", "0"]))


# --- --skip ---

def test_skip_enables_config():
    cfg = linecount_from_args(parse(["--skip", "5"]))
    assert cfg.enabled is True
    assert cfg.offset == 5


def test_skip_zero_leaves_disabled():
    cfg = linecount_from_args(parse(["--skip", "0"]))
    assert cfg.enabled is False


# --- combined ---

def test_head_and_skip_combined():
    cfg = linecount_from_args(parse(["--head", "20", "--skip", "3"]))
    assert cfg.enabled is True
    assert cfg.max_lines == 20
    assert cfg.offset == 3
