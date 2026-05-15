"""Tests for logslice.multiline_cli."""
from __future__ import annotations

import argparse

import pytest

from logslice.multiline import MultilineConfig
from logslice.multiline_cli import add_multiline_args, multiline_from_args


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_multiline_args(p)
    return p


def parse(args: list[str]) -> argparse.Namespace:
    return build_parser().parse_args(args)


def test_no_args_produces_disabled_config() -> None:
    cfg = multiline_from_args(parse([]))
    assert isinstance(cfg, MultilineConfig)
    assert cfg.enabled is False


def test_ml_start_enables_config() -> None:
    cfg = multiline_from_args(parse(["--ml-start", r"^ERROR"]))
    assert cfg.enabled is True
    assert cfg.start_pattern == r"^ERROR"


def test_ml_cont_enables_config() -> None:
    cfg = multiline_from_args(parse(["--ml-cont", r"^\s+"]))
    assert cfg.enabled is True
    assert cfg.continuation_pattern == r"^\s+"


def test_both_patterns_set_correctly() -> None:
    cfg = multiline_from_args(
        parse(["--ml-start", r"^BEGIN", "--ml-cont", r"^-"])
    )
    assert cfg.start_pattern == r"^BEGIN"
    assert cfg.continuation_pattern == r"^-"


def test_max_lines_default_is_zero() -> None:
    cfg = multiline_from_args(parse(["--ml-start", r"^E"]))
    assert cfg.max_lines == 0


def test_max_lines_is_parsed() -> None:
    cfg = multiline_from_args(parse(["--ml-start", r"^E", "--ml-max-lines", "10"]))
    assert cfg.max_lines == 10


def test_join_str_default_is_newline() -> None:
    cfg = multiline_from_args(parse(["--ml-start", r"^E"]))
    assert cfg.join_str == "\n"


def test_custom_join_str_is_set() -> None:
    cfg = multiline_from_args(
        parse(["--ml-start", r"^E", "--ml-join", " | "])
    )
    assert cfg.join_str == " | "
