"""Output formatting for matched log lines."""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from logslice.filter import LogMatch
from logslice.highlighter import HighlightConfig, LogHighlighter


class OutputFormat(str, Enum):
    PLAIN = "plain"
    JSON = "json"
    COLOR = "color"


class LogFormatter:
    """Formats LogMatch objects for terminal or structured output."""

    def __init__(
        self,
        fmt: OutputFormat = OutputFormat.PLAIN,
        show_line_numbers: bool = True,
        show_source: bool = True,
        highlight_config: Optional[HighlightConfig] = None,
    ) -> None:
        self.fmt = fmt
        self.show_line_numbers = show_line_numbers
        self.show_source = show_source
        self.highlighter = LogHighlighter(highlight_config or HighlightConfig())

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def format_match(self, match: LogMatch) -> str:
        if self.fmt == OutputFormat.JSON:
            return self._format_json(match)
        if self.fmt == OutputFormat.COLOR:
            return self._format_color(match)
        return self._format_plain(match)

    def _format_plain(self, match: LogMatch) -> str:
        parts = []
        if self.show_source:
            parts.append(f"[{match.source}]")
        if self.show_line_numbers:
            parts.append(f"{match.line_number}:")
        parts.append(match.line)
        return " ".join(parts)

    def _format_color(self, match: LogMatch) -> str:
        highlighted = self.highlighter.highlight_line(
            match.line, pattern=match.matched_pattern
        )
        parts = []
        if self.show_source:
            parts.append(f"[{match.source}]")
        if self.show_line_numbers:
            parts.append(f"{match.line_number}:")
        parts.append(highlighted)
        return " ".join(parts)

    def _format_json(self, match: LogMatch) -> str:
        data = match.to_dict()
        data["timestamp"] = self._get_timestamp()
        return json.dumps(data)

    def format_all(self, matches: list) -> list:
        return [self.format_match(m) for m in matches]
