"""Integration tests: multiline aggregator wired into a simple pipeline."""
from __future__ import annotations

from logslice.multiline import LogMultilineAggregator, MultilineConfig
from logslice.filter import FilterConfig, LogFilter


def run(lines: list[str], start: str, cont: str, include: str | None = None) -> list[str]:
    """Aggregate *lines* then optionally filter with *include* pattern."""
    agg = LogMultilineAggregator(
        MultilineConfig(enabled=True, start_pattern=start, continuation_pattern=cont)
    )
    aggregated = list(agg.process(iter(lines)))

    if include is None:
        return aggregated

    filt = LogFilter(FilterConfig(include_patterns=[include]))
    results = []
    for i, line in enumerate(aggregated, start=1):
        match = filt.match(line, line_number=i)
        if match:
            results.append(match.line)
    return results


def test_java_stacktrace_aggregated_as_single_event() -> None:
    lines = [
        "INFO  request received",
        "ERROR NullPointerException",
        "\tat com.example.Foo.bar(Foo.java:42)",
        "\tat com.example.Main.main(Main.java:10)",
        "INFO  request completed",
    ]
    result = run(lines, start=r"^ERROR", cont=r"^\t")
    assert len(result) == 3
    assert "NullPointerException" in result[1]
    assert "Foo.java:42" in result[1]


def test_filter_applied_after_aggregation() -> None:
    lines = [
        "DEBUG heartbeat",
        "ERROR boom",
        "  detail1",
        "  detail2",
        "DEBUG heartbeat",
    ]
    result = run(lines, start=r"^ERROR", cont=r"^  ", include=r"ERROR")
    assert len(result) == 1
    assert "detail1" in result[0]


def test_no_matching_start_lines_passes_all_as_individual() -> None:
    lines = ["alpha", "beta", "gamma"]
    agg = LogMultilineAggregator(
        MultilineConfig(enabled=True, start_pattern=r"^NEVER", continuation_pattern=r"^X")
    )
    result = list(agg.process(iter(lines)))
    assert result == lines


def test_multiple_events_separated_correctly() -> None:
    lines = [
        "START a",
        "-a1",
        "START b",
        "-b1",
        "-b2",
    ]
    agg = LogMultilineAggregator(
        MultilineConfig(enabled=True, start_pattern=r"^START", continuation_pattern=r"^-")
    )
    result = list(agg.process(iter(lines)))
    assert result == ["START a\n-a1", "START b\n-b1\n-b2"]
