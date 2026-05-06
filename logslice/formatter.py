"""Output formatters for log matches."""

import json
from datetime import datetime
from typing import List

from logslice.filter import LogMatch


class OutputFormat:
    PLAIN = "plain"
    JSON = "json"
    CSV = "csv"


class LogFormatter:
    """Formats LogMatch results into various output formats."""

    def __init__(self, fmt: str = OutputFormat.PLAIN, show_line_numbers: bool = True,
                 show_source: bool = True, timestamp: bool = False):
        if fmt not in (OutputFormat.PLAIN, OutputFormat.JSON, OutputFormat.CSV):
            raise ValueError(f"Unsupported format: {fmt!r}")
        self.fmt = fmt
        self.show_line_numbers = show_line_numbers
        self.show_source = show_source
        self.timestamp = timestamp

    def _get_timestamp(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def format_match(self, match: LogMatch) -> str:
        """Format a single LogMatch to a string."""
        if self.fmt == OutputFormat.JSON:
            data = match.to_dict()
            if self.timestamp:
                data["formatted_at"] = self._get_timestamp()
            return json.dumps(data)

        if self.fmt == OutputFormat.CSV:
            source = match.source or ""
            line = match.line.replace(",", "\\,").replace("\n", "")
            return f"{match.line_number},{source},{line}"

        # PLAIN
        parts = []
        if self.show_line_numbers:
            parts.append(f"[{match.line_number}]")
        if self.show_source and match.source:
            parts.append(f"({match.source})")
        parts.append(match.line.rstrip("\n"))
        return " ".join(parts)

    def format_matches(self, matches: List[LogMatch]) -> List[str]:
        """Format a list of LogMatch objects."""
        return [self.format_match(m) for m in matches]

    def csv_header(self) -> str:
        """Return the CSV header line."""
        return "line_number,source,line"
