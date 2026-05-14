"""Checkpoint integration: resume log processing from a saved bookmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Tuple

from logslice.bookmark import Bookmark, BookmarkConfig, LogBookmark


@dataclass
class CheckpointConfig:
    enabled: bool = False
    store_dir: str = ".logslice_bookmarks"
    auto_save: bool = True


class LogCheckpoint:
    """Wraps a LogBookmark to skip already-processed lines and auto-save progress."""

    def __init__(self, config: CheckpointConfig) -> None:
        self._config = config
        self._bookmark = LogBookmark(
            BookmarkConfig(enabled=config.enabled, store_dir=config.store_dir)
        )

    @property
    def config(self) -> CheckpointConfig:
        return self._config

    def resume_from(self, source: str) -> int:
        """Return the line number to resume from (0 = start from beginning)."""
        if not self._config.enabled:
            return 0
        bm = self._bookmark.load(source)
        return bm.line_number if bm else 0

    def filter_lines(
        self,
        source: str,
        lines: Iterable[Tuple[int, str]],
    ) -> Iterator[Tuple[int, str]]:
        """Yield (line_number, line) tuples, skipping already-seen lines."""
        resume = self.resume_from(source)
        for lineno, line in lines:
            if lineno <= resume:
                continue
            yield lineno, line
            if self._config.auto_save:
                self._bookmark.save(source, line_number=lineno)

    def save(self, source: str, line_number: int, byte_offset: int = 0) -> None:
        self._bookmark.save(source, line_number=line_number, byte_offset=byte_offset)

    def reset(self, source: str) -> None:
        self._bookmark.clear(source)
