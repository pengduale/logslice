"""Log tailing functionality for logslice."""

import time
import os
from typing import Iterator, Optional
from dataclasses import dataclass

from logslice.filter import LogFilter, LogMatch, FilterConfig


@dataclass
class TailConfig:
    """Configuration for log tailing behavior."""
    poll_interval: float = 0.1
    follow: bool = True
    initial_lines: Optional[int] = None


class LogTailer:
    """Tails a log file, optionally filtering lines using LogFilter."""

    def __init__(self, filepath: str, filter_config: FilterConfig, tail_config: Optional[TailConfig] = None):
        self.filepath = filepath
        self.filter = LogFilter(filter_config)
        self.tail_config = tail_config or TailConfig()
        self._stop = False

    def stop(self) -> None:
        """Signal the tailer to stop."""
        self._stop = True

    def _read_initial_lines(self, file) -> list[str]:
        """Read the last N lines from the file if initial_lines is set."""
        if self.tail_config.initial_lines is None:
            return []
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        block_size = 4096
        lines = []
        pos = file_size
        while pos > 0 and len(lines) <= self.tail_config.initial_lines:
            read_size = min(block_size, pos)
            pos -= read_size
            file.seek(pos)
            chunk = file.read(read_size)
            lines = chunk.splitlines() + lines
        return lines[-self.tail_config.initial_lines:] if self.tail_config.initial_lines else []

    def tail(self) -> Iterator[LogMatch]:
        """Yield filtered LogMatch objects from the tailed file."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Log file not found: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8", errors="replace") as f:
            initial = self._read_initial_lines(f)
            line_number = 1

            for raw_line in initial:
                match = self.filter.check_line(raw_line, line_number, self.filepath)
                if match:
                    yield match
                line_number += 1

            if self.tail_config.initial_lines is not None:
                f.seek(0, os.SEEK_END)

            while not self._stop:
                raw_line = f.readline()
                if raw_line:
                    line = raw_line.rstrip("\n")
                    match = self.filter.check_line(line, line_number, self.filepath)
                    if match:
                        yield match
                    line_number += 1
                elif not self.tail_config.follow:
                    break
                else:
                    time.sleep(self.tail_config.poll_interval)
