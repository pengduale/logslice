"""Tests for logslice.severity_cli."""

import argparse
import pytest

from logslice.severity import Level
from logslice.severity_cli import add_severity_args, severity_filter_from_args


def parse(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_severity_args(parser)
    return parser.parse_args(args)


def test_no_args_produces_disabled_filter():
    ns = parse([])
    f = severity_filter_from_args(ns)
    assert not f.config.enabled


def test_min_level_enables_filter():
    ns = parse(["--min-level", "WARNING"])
    f = severity_filter_from_args(ns)
    assert f.config.enabled
    assert f.config.min_level == Level.WARNING
    assert f.config.max_level == Level.CRITICAL


def test_max_level_enables_filter():
    ns = parse(["--max-level", "ERROR"])
    f = severity_filter_from_args(ns)
    assert f.config.enabled
    assert f.config.min_level == Level.DEBUG
    assert f.config.max_level == Level.ERROR


def test_both_levels_set_correctly():
    ns = parse(["--min-level", "INFO", "--max-level", "ERROR"])
    f = severity_filter_from_args(ns)
    assert f.config.min_level == Level.INFO
    assert f.config.max_level == Level.ERROR


def test_invalid_level_name_raises():
    ns = parse(["--min-level", "VERBOSE"])
    with pytest.raises(ValueError, match="Unknown log level"):
        severity_filter_from_args(ns)


def test_disabled_filter_passes_everything():
    ns = parse([])
    f = severity_filter_from_args(ns)
    assert f.process("DEBUG noisy") == "DEBUG noisy"
    assert f.process("ERROR boom") == "ERROR boom"


def test_enabled_filter_rejects_below_min():
    ns = parse(["--min-level", "ERROR"])
    f = severity_filter_from_args(ns)
    assert f.process("INFO just info") is None
    assert f.process("ERROR critical failure") == "ERROR critical failure"
