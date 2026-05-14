"""Bookmark support: persist and restore the last-read position in a log file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BookmarkConfig:
    enabled: bool = False
    store_dir: str = ".logslice_bookmarks"

    def __post_init__(self) -> None:
        if self.enabled and not self.store_dir:
            raise ValueError("store_dir must not be empty when bookmarks are enabled")


@dataclass
class Bookmark:
    source: str
    line_number: int = 0
    byte_offset: int = 0

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "line_number": self.line_number,
            "byte_offset": self.byte_offset,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bookmark":
        return cls(
            source=data["source"],
            line_number=data.get("line_number", 0),
            byte_offset=data.get("byte_offset", 0),
        )


class LogBookmark:
    """Persists and restores read positions for log sources."""

    def __init__(self, config: BookmarkConfig) -> None:
        self._config = config
        self._bookmarks: dict[str, Bookmark] = {}
        if config.enabled:
            os.makedirs(config.store_dir, exist_ok=True)

    @property
    def config(self) -> BookmarkConfig:
        return self._config

    def _path_for(self, source: str) -> Path:
        safe = source.replace("/", "_").replace("\\", "_").strip("_") or "stdin"
        return Path(self._config.store_dir) / f"{safe}.json"

    def load(self, source: str) -> Optional[Bookmark]:
        if not self._config.enabled:
            return None
        p = self._path_for(source)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
            bm = Bookmark.from_dict(data)
            self._bookmarks[source] = bm
            return bm
        except (json.JSONDecodeError, KeyError):
            return None

    def save(self, source: str, line_number: int, byte_offset: int = 0) -> None:
        if not self._config.enabled:
            return
        bm = Bookmark(source=source, line_number=line_number, byte_offset=byte_offset)
        self._bookmarks[source] = bm
        self._path_for(source).write_text(json.dumps(bm.to_dict(), indent=2))

    def clear(self, source: str) -> None:
        if not self._config.enabled:
            return
        p = self._path_for(source)
        if p.exists():
            p.unlink()
        self._bookmarks.pop(source, None)

    def get(self, source: str) -> Optional[Bookmark]:
        return self._bookmarks.get(source)
