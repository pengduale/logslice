"""Tests for logslice.bookmark."""

import json
import pytest
from pathlib import Path

from logslice.bookmark import Bookmark, BookmarkConfig, LogBookmark


@pytest.fixture
def store_dir(tmp_path) -> str:
    return str(tmp_path / "bm_store")


def make_bookmark(enabled: bool = True, store_dir: str = "/tmp/bm_test", tmp=None) -> LogBookmark:
    if tmp is not None:
        store_dir = str(tmp)
    return LogBookmark(BookmarkConfig(enabled=enabled, store_dir=store_dir))


def test_invalid_store_dir_raises():
    with pytest.raises(ValueError, match="store_dir"):
        BookmarkConfig(enabled=True, store_dir="")


def test_disabled_load_returns_none(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=False, store_dir=str(tmp_path)))
    assert bm.load("myfile.log") is None


def test_disabled_save_does_nothing(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=False, store_dir=str(tmp_path)))
    bm.save("myfile.log", line_number=42)
    assert not any(tmp_path.iterdir())


def test_load_returns_none_for_unknown_source(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=True, store_dir=str(tmp_path)))
    assert bm.load("unknown.log") is None


def test_save_and_load_roundtrip(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=True, store_dir=str(tmp_path)))
    bm.save("app.log", line_number=100, byte_offset=2048)
    loaded = bm.load("app.log")
    assert loaded is not None
    assert loaded.source == "app.log"
    assert loaded.line_number == 100
    assert loaded.byte_offset == 2048


def test_save_creates_json_file(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=True, store_dir=str(tmp_path)))
    bm.save("server.log", line_number=7)
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["line_number"] == 7


def test_clear_removes_file(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=True, store_dir=str(tmp_path)))
    bm.save("app.log", line_number=5)
    bm.clear("app.log")
    assert bm.load("app.log") is None
    assert not any(tmp_path.iterdir())


def test_clear_nonexistent_does_not_raise(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=True, store_dir=str(tmp_path)))
    bm.clear("ghost.log")  # should not raise


def test_get_returns_in_memory_bookmark(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=True, store_dir=str(tmp_path)))
    assert bm.get("app.log") is None
    bm.save("app.log", line_number=3)
    assert bm.get("app.log") is not None
    assert bm.get("app.log").line_number == 3


def test_bookmark_to_dict():
    b = Bookmark(source="x.log", line_number=10, byte_offset=512)
    d = b.to_dict()
    assert d == {"source": "x.log", "line_number": 10, "byte_offset": 512}


def test_bookmark_from_dict_roundtrip():
    original = Bookmark(source="y.log", line_number=99, byte_offset=1024)
    restored = Bookmark.from_dict(original.to_dict())
    assert restored.source == original.source
    assert restored.line_number == original.line_number
    assert restored.byte_offset == original.byte_offset


def test_corrupted_bookmark_file_returns_none(tmp_path):
    bm = LogBookmark(BookmarkConfig(enabled=True, store_dir=str(tmp_path)))
    p = tmp_path / "app_log.json"
    p.write_text("not-json{{{")
    result = bm.load("app.log")
    assert result is None
