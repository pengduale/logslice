"""Tests for logslice.checkpoint."""

import pytest

from logslice.checkpoint import CheckpointConfig, LogCheckpoint


def make_checkpoint(tmp_path, enabled: bool = True, auto_save: bool = True) -> LogCheckpoint:
    return LogCheckpoint(
        CheckpointConfig(enabled=enabled, store_dir=str(tmp_path), auto_save=auto_save)
    )


def numbered(lines):
    return list(enumerate(lines, start=1))


def test_disabled_resume_returns_zero(tmp_path):
    cp = make_checkpoint(tmp_path, enabled=False)
    assert cp.resume_from("app.log") == 0


def test_no_bookmark_resumes_from_zero(tmp_path):
    cp = make_checkpoint(tmp_path)
    assert cp.resume_from("app.log") == 0


def test_disabled_passes_all_lines(tmp_path):
    cp = make_checkpoint(tmp_path, enabled=False)
    pairs = numbered(["line1", "line2", "line3"])
    result = list(cp.filter_lines("app.log", pairs))
    assert result == pairs


def test_first_run_passes_all_lines(tmp_path):
    cp = make_checkpoint(tmp_path)
    pairs = numbered(["a", "b", "c"])
    result = list(cp.filter_lines("app.log", pairs))
    assert result == pairs


def test_auto_save_updates_position(tmp_path):
    cp = make_checkpoint(tmp_path, auto_save=True)
    pairs = numbered(["x", "y", "z"])
    list(cp.filter_lines("app.log", pairs))
    assert cp.resume_from("app.log") == 3


def test_second_run_skips_seen_lines(tmp_path):
    cp = make_checkpoint(tmp_path, auto_save=True)
    pairs = numbered(["a", "b", "c", "d"])
    list(cp.filter_lines("app.log", pairs))

    cp2 = make_checkpoint(tmp_path, auto_save=True)
    new_pairs = numbered(["a", "b", "c", "d", "e", "f"])
    result = list(cp2.filter_lines("app.log", new_pairs))
    assert result == [(5, "e"), (6, "f")]


def test_no_auto_save_does_not_persist(tmp_path):
    cp = make_checkpoint(tmp_path, auto_save=False)
    pairs = numbered(["p", "q", "r"])
    list(cp.filter_lines("app.log", pairs))
    assert cp.resume_from("app.log") == 0


def test_manual_save_persists_position(tmp_path):
    cp = make_checkpoint(tmp_path, auto_save=False)
    cp.save("app.log", line_number=10)
    assert cp.resume_from("app.log") == 10


def test_reset_clears_position(tmp_path):
    cp = make_checkpoint(tmp_path, auto_save=True)
    pairs = numbered(["1", "2", "3"])
    list(cp.filter_lines("app.log", pairs))
    cp.reset("app.log")
    assert cp.resume_from("app.log") == 0


def test_multiple_sources_tracked_independently(tmp_path):
    cp = make_checkpoint(tmp_path, auto_save=True)
    list(cp.filter_lines("a.log", numbered(["x", "y"])))
    list(cp.filter_lines("b.log", numbered(["1"])))
    assert cp.resume_from("a.log") == 2
    assert cp.resume_from("b.log") == 1
