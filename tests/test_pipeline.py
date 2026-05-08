"""Tests for LogPipeline."""
from __future__ import annotations

import json

import pytest

from logslice.filter import FilterConfig
from logslice.formatter import OutputFormat
from logslice.highlighter import HighlightConfig
from logslice.pipeline import LogPipeline, PipelineConfig


def make_pipeline(**kwargs) -> LogPipeline:
    cfg = PipelineConfig(**kwargs)
    return LogPipeline(cfg)


LINES = ["INFO  server started", "ERROR disk full", "WARN  low memory", "DEBUG tick"]


def test_no_filter_passes_all_lines():
    pipe = make_pipeline(show_source=False)
    results = list(pipe.process(LINES))
    assert len(results) == 4


def test_include_pattern_filters_lines():
    fc = FilterConfig(include_patterns=["ERROR"])
    pipe = make_pipeline(filter_config=fc, show_source=False)
    results = list(pipe.process(LINES))
    assert len(results) == 1
    assert "ERROR disk full" in results[0]


def test_exclude_pattern_removes_lines():
    fc = FilterConfig(exclude_patterns=["DEBUG"])
    pipe = make_pipeline(filter_config=fc, show_source=False)
    results = list(pipe.process(LINES))
    assert len(results) == 3
    assert all("DEBUG" not in r for r in results)


def test_json_output_is_valid_json():
    pipe = make_pipeline(output_format=OutputFormat.JSON, show_source=False)
    results = list(pipe.process(["hello world"]))
    assert len(results) == 1
    data = json.loads(results[0])
    assert data["line"] == "hello world"


def test_stats_are_recorded():
    fc = FilterConfig(include_patterns=["ERROR"])
    pipe = make_pipeline(filter_config=fc)
    list(pipe.process(LINES))
    pipe.finish()
    assert pipe.stats.total_lines == 4
    assert pipe.stats.matched_lines == 1


def test_source_name_injected_into_match():
    pipe = make_pipeline(
        source_name="app.log",
        output_format=OutputFormat.JSON,
        show_source=True,
    )
    results = list(pipe.process(["hello"]))
    data = json.loads(results[0])
    assert data["source"] == "app.log"


def test_highlight_applied_in_plain_output():
    hc = HighlightConfig(enabled=True, pattern="ERROR")
    fc = FilterConfig(include_patterns=["ERROR"])
    pipe = make_pipeline(
        filter_config=fc,
        highlight_config=hc,
        show_source=False,
        output_format=OutputFormat.PLAIN,
    )
    results = list(pipe.process(["ERROR disk full"]))
    assert "\033[" in results[0]  # ANSI escape present


def test_finish_sets_elapsed_time():
    pipe = make_pipeline()
    list(pipe.process(LINES))
    pipe.finish()
    assert pipe.stats.elapsed_seconds() >= 0
