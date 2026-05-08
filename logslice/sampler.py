"""Log line sampler — keeps every Nth matching line to reduce output volume."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SamplerConfig:
    """Configuration for the log sampler."""

    enabled: bool = False
    rate: int = 1  # keep every Nth line (1 = keep all, 2 = keep every other, etc.)
    max_lines: Optional[int] = None  # hard cap on total lines emitted

    def __post_init__(self) -> None:
        if self.rate < 1:
            raise ValueError(f"Sampler rate must be >= 1, got {self.rate}")
        if self.max_lines is not None and self.max_lines < 1:
            raise ValueError(f"max_lines must be >= 1, got {self.max_lines}")


class LogSampler:
    """Samples log lines according to a configured rate and optional line cap."""

    def __init__(self, config: SamplerConfig) -> None:
        self._config = config
        self._seen: int = 0   # total lines offered
        self._emitted: int = 0  # total lines passed through

    @property
    def config(self) -> SamplerConfig:
        return self._config

    @property
    def seen(self) -> int:
        return self._seen

    @property
    def emitted(self) -> int:
        return self._emitted

    def process(self, line: str) -> Optional[str]:
        """Return the line if it should be emitted, otherwise None."""
        if not self._config.enabled:
            return line

        self._seen += 1

        # Hard cap reached — suppress everything further
        if self._config.max_lines is not None and self._emitted >= self._config.max_lines:
            return None

        # Rate sampling: emit only when seen count is a multiple of rate
        if self._seen % self._config.rate != 0:
            return None

        self._emitted += 1
        return line

    def summary(self) -> str:
        """Return a human-readable sampling summary."""
        suppressed = self._seen - self._emitted
        return (
            f"Sampler: seen={self._seen}, emitted={self._emitted}, "
            f"suppressed={suppressed}, rate=1/{self._config.rate}"
        )
