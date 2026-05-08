"""Utilities for reading log lines from files or stdin."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, Optional


class LogReader:
    """Reads lines from a file path or stdin.

    Parameters
    ----------
    path:
        Path to the log file.  Pass ``None`` to read from *stdin*.
    encoding:
        File encoding (default ``utf-8``).
    errors:
        How to handle decode errors (default ``replace``).
    """

    def __init__(
        self,
        path: Optional[Path] = None,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> None:
        self._path = path
        self._encoding = encoding
        self._errors = errors

    # ------------------------------------------------------------------
    @property
    def source_name(self) -> str:
        """Human-readable name for the source (filename or '<stdin>')."""
        return self._path.name if self._path else "<stdin>"

    def lines(self) -> Iterator[str]:
        """Yield lines from the configured source."""
        if self._path is None:
            yield from self._read_stdin()
        else:
            yield from self._read_file()

    # ------------------------------------------------------------------
    def _read_file(self) -> Iterator[str]:
        if not self._path.exists():
            raise FileNotFoundError(f"Log file not found: {self._path}")
        with self._path.open(encoding=self._encoding, errors=self._errors) as fh:
            for line in fh:
                yield line

    def _read_stdin(self) -> Iterator[str]:
        for line in sys.stdin:
            yield line
