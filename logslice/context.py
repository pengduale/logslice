"""Context lines support: capture N lines before/after each match."""
from dataclasses import dataclass, field
from collections import deque
from typing import Iterator, List, Optional
from logslice.filter import LogMatch


@dataclass
class ContextConfig:
    before: int = 0
    after: int = 0
    separator: str = "--"

    def __post_init__(self) -> None:
        if self.before < 0:
            raise ValueError("before must be >= 0")
        if self.after < 0:
            raise ValueError("after must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.before > 0 or self.after > 0


@dataclass
class _PendingAfter:
    match: LogMatch
    remaining: int


class ContextCollector:
    """Wraps a stream of LogMatch objects and yields context lines around matches."""

    def __init__(self, config: ContextConfig) -> None:
        self._config = config
        self._before_buf: deque = deque(maxlen=max(config.before, 1))
        self._pending_after: List[_PendingAfter] = []
        self._emitted_line_numbers: set = set()
        self._last_emitted: Optional[int] = None

    def feed(self, match: Optional[LogMatch], line_text: str, line_number: int) -> Iterator[LogMatch]:
        """Feed a line (matched or not) and yield context-enriched LogMatch objects."""
        cfg = self._config

        # Decrement after-counters and emit context lines for previous matches
        still_pending = []
        for pending in self._pending_after:
            if pending.remaining > 0 and line_number not in self._emitted_line_numbers:
                ctx = LogMatch(
                    line=line_text,
                    line_number=line_number,
                    source=pending.match.source,
                    matched_patterns=pending.match.matched_patterns,
                    context_tag="after",
                )
                self._emit_separator_if_needed(line_number)
                yield ctx
                self._emitted_line_numbers.add(line_number)
                self._last_emitted = line_number
            pending.remaining -= 1
            if pending.remaining >= 0:
                still_pending.append(pending)
        self._pending_after = still_pending

        if match is not None:
            # Emit before-context
            for prev_text, prev_num in list(self._before_buf):
                if prev_num not in self._emitted_line_numbers:
                    self._emit_separator_if_needed(prev_num)
                    yield LogMatch(
                        line=prev_text,
                        line_number=prev_num,
                        source=match.source,
                        matched_patterns=match.matched_patterns,
                        context_tag="before",
                    )
                    self._emitted_line_numbers.add(prev_num)
                    self._last_emitted = prev_num

            # Emit the match itself
            if line_number not in self._emitted_line_numbers:
                self._emit_separator_if_needed(line_number)
                yield match
                self._emitted_line_numbers.add(line_number)
                self._last_emitted = line_number

            if cfg.after > 0:
                self._pending_after.append(_PendingAfter(match=match, remaining=cfg.after))

        # Always buffer non-matched lines for before-context
        if match is None:
            self._before_buf.append((line_text, line_number))

    def _emit_separator_if_needed(self, line_number: int) -> None:
        """Track whether a separator should be printed (side-effect free here; handled by caller)."""
        pass  # Separator logic delegated to formatter/pipeline
