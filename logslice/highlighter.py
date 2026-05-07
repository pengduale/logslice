"""Terminal color highlighting for matched log lines."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class Color(str, Enum):
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


@dataclass
class HighlightConfig:
    enabled: bool = True
    match_color: Color = Color.YELLOW
    line_color: Optional[Color] = None
    bold_matches: bool = True


class LogHighlighter:
    """Applies terminal color codes to log lines based on regex matches."""

    def __init__(self, config: Optional[HighlightConfig] = None) -> None:
        self.config = config or HighlightConfig()

    def highlight_line(self, line: str, pattern: Optional[str] = None) -> str:
        """Return the line with color codes applied."""
        if not self.config.enabled:
            return line

        result = line

        if pattern:
            result = self._highlight_matches(result, pattern)

        if self.config.line_color:
            result = f"{self.config.line_color}{result}{Color.RESET}"

        return result

    def _highlight_matches(self, line: str, pattern: str) -> str:
        """Wrap regex match spans with color codes."""
        try:
            regex = re.compile(pattern)
        except re.error:
            return line

        prefix = ""
        if self.config.bold_matches:
            prefix = f"{Color.BOLD}{self.config.match_color}"
        else:
            prefix = str(self.config.match_color)

        suffix = Color.RESET

        return regex.sub(lambda m: f"{prefix}{m.group()}{suffix}", line)

    def strip_colors(self, line: str) -> str:
        """Remove all ANSI escape codes from a string."""
        ansi_escape = re.compile(r"\033\[[0-9;]*m")
        return ansi_escape.sub("", line)
