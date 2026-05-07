"""Tests for logslice.tailer module."""

import os
import tempfile
import threading
import time
import pytest

from logslice.filter import FilterConfig
from logslice.tailer import LogTailer, TailConfig


def write_lines(filepath: str, lines: list[str]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def make_tailer(filepath, include=None, exclude=None, follow=False, initial_lines=None):
    filter_config = FilterConfig(include_patterns=include or [], exclude_patterns=exclude or [])
    tail_config = TailConfig(follow=follow, initial_lines=initial_lines, poll_interval=0.05)
    return LogTailer(filepath, filter_config, tail_config)


def test_tailer_raises_for_missing_file():
    tailer = make_tailer("/nonexistent/path/to/logfile.log")
    with pytest.raises(FileNotFoundError):
        list(tailer.tail())


def test_tailer_reads_all_lines_no_filter():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write("line one\nline two\nline three\n")
        path = f.name
    try:
        tailer = make_tailer(path)
        results = list(tailer.tail())
        assert len(results) == 3
        assert results[0].line == "line one"
        assert results[2].line == "line three"
    finally:
        os.unlink(path)


def test_tailer_filters_with_include_pattern():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write("ERROR something failed\nINFO all good\nERROR another error\n")
        path = f.name
    try:
        tailer = make_tailer(path, include=["ERROR"])
        results = list(tailer.tail())
        assert len(results) == 2
        assert all("ERROR" in r.line for r in results)
    finally:
        os.unlink(path)


def test_tailer_filters_with_exclude_pattern():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write("DEBUG verbose\nINFO useful\nDEBUG more noise\n")
        path = f.name
    try:
        tailer = make_tailer(path, exclude=["DEBUG"])
        results = list(tailer.tail())
        assert len(results) == 1
        assert results[0].line == "INFO useful"
    finally:
        os.unlink(path)


def test_tailer_follow_picks_up_new_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write("initial line\n")
        path = f.name
    try:
        tailer = make_tailer(path, follow=True)
        collected = []

        def run():
            for match in tailer.tail():
                collected.append(match)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        time.sleep(0.1)

        with open(path, "a", encoding="utf-8") as f:
            f.write("appended line\n")

        time.sleep(0.2)
        tailer.stop()
        t.join(timeout=1.0)

        lines = [m.line for m in collected]
        assert "initial line" in lines
        assert "appended line" in lines
    finally:
        os.unlink(path)
