"""Tests for the logslice CLI entry point."""

import json
from pathlib import Path

import pytest

from logslice.cli import run


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    path = tmp_path / "app.log"
    lines = [
        "INFO  server started",
        "DEBUG loading config",
        "ERROR failed to connect",
        "INFO  request received",
        "WARNING disk space low",
    ]
    path.write_text("\n".join(lines) + "\n")
    return path


def test_missing_file_returns_exit_code_1(tmp_path: Path) -> None:
    result = run([str(tmp_path / "nonexistent.log")])
    assert result == 1


def test_reads_all_lines_by_default(log_file: Path, capsys) -> None:
    result = run([str(log_file)])
    assert result == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l]
    assert len(lines) == 5


def test_include_pattern_filters_output(log_file: Path, capsys) -> None:
    result = run([str(log_file), "--include", "ERROR"])
    assert result == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l]
    assert len(lines) == 1
    assert "ERROR" in lines[0]


def test_exclude_pattern_removes_lines(log_file: Path, capsys) -> None:
    result = run([str(log_file), "--exclude", "DEBUG"])
    assert result == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l]
    assert all("DEBUG" not in l for l in lines)
    assert len(lines) == 4


def test_json_format_produces_valid_json(log_file: Path, capsys) -> None:
    result = run([str(log_file), "--format", "json", "--include", "INFO"])
    assert result == 0
    captured = capsys.readouterr()
    output_lines = [l for l in captured.out.splitlines() if l]
    assert len(output_lines) == 2
    for raw in output_lines:
        obj = json.loads(raw)
        assert "line" in obj
        assert "line_number" in obj


def test_no_line_numbers_flag(log_file: Path, capsys) -> None:
    result = run([str(log_file), "--no-line-numbers", "--include", "ERROR"])
    assert result == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l]
    assert len(lines) == 1
    # plain format with no line numbers should not contain a leading digit block
    assert not lines[0].startswith("[") or "ERROR" in lines[0]


def test_no_source_flag(log_file: Path, capsys) -> None:
    result = run([str(log_file), "--no-source", "--include", "WARNING"])
    assert result == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l]
    assert len(lines) == 1
    assert "app.log" not in lines[0]


def test_multiple_include_patterns(log_file: Path, capsys) -> None:
    result = run([str(log_file), "--include", "ERROR", "--include", "WARNING"])
    assert result == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l]
    assert len(lines) == 2
