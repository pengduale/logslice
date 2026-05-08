"""Tests for LogReader."""
from __future__ import annotations

import io
from pathlib import Path

import pytest

from logslice.reader import LogReader


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("line one\nline two\nline three\n", encoding="utf-8")
    return p


def test_reads_all_lines_from_file(log_file: Path):
    reader = LogReader(path=log_file)
    lines = list(reader.lines())
    assert len(lines) == 3
    assert lines[0].rstrip() == "line one"


def test_source_name_is_filename(log_file: Path):
    reader = LogReader(path=log_file)
    assert reader.source_name == log_file.name


def test_source_name_stdin():
    reader = LogReader(path=None)
    assert reader.source_name == "<stdin>"


def test_raises_for_missing_file(tmp_path: Path):
    reader = LogReader(path=tmp_path / "missing.log")
    with pytest.raises(FileNotFoundError, match="missing.log"):
        list(reader.lines())


def test_reads_stdin(monkeypatch: pytest.MonkeyPatch):
    fake_stdin = io.StringIO("stdin line 1\nstdin line 2\n")
    monkeypatch.setattr("sys.stdin", fake_stdin)
    reader = LogReader(path=None)
    lines = list(reader.lines())
    assert len(lines) == 2
    assert lines[0].rstrip() == "stdin line 1"


def test_handles_encoding_errors(tmp_path: Path):
    p = tmp_path / "bad.log"
    p.write_bytes(b"good line\nba\xffd line\n")
    reader = LogReader(path=p, encoding="utf-8", errors="replace")
    lines = list(reader.lines())
    assert len(lines) == 2  # both lines returned despite bad bytes
