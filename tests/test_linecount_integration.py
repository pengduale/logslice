"""Integration tests: LogLineCounter wired into a simple pipeline."""

from logslice.linecount import LineCountConfig, LogLineCounter


def run_counter(lines: list, **kwargs) -> list:
    """Feed *lines* through a counter and return non-None, non-stopped results."""
    counter = LogLineCounter(LineCountConfig(**kwargs))
    out = []
    for line in lines:
        result = counter.process(line)
        if result is None or result.stopped:
            break
        out.append(result)
    return out


SAMPLE = [f"2024-01-01 INFO message {i}" for i in range(10)]


def test_no_limit_passes_all():
    results = run_counter(SAMPLE)
    assert len(results) == 10


def test_head_5_returns_first_5():
    results = run_counter(SAMPLE, enabled=True, max_lines=5)
    assert len(results) == 5
    assert results[0].line == SAMPLE[0]
    assert results[4].line == SAMPLE[4]


def test_skip_3_omits_first_3():
    results = run_counter(SAMPLE, enabled=True, offset=3)
    assert len(results) == 7
    assert results[0].line == SAMPLE[3]


def test_skip_2_head_4_returns_correct_slice():
    results = run_counter(SAMPLE, enabled=True, offset=2, max_lines=4)
    assert len(results) == 4
    assert [r.line for r in results] == SAMPLE[2:6]


def test_line_numbers_are_absolute_with_offset():
    results = run_counter(SAMPLE, enabled=True, offset=3)
    assert results[0].line_number == 4
    assert results[1].line_number == 5


def test_empty_input_returns_empty():
    results = run_counter([], enabled=True, max_lines=5)
    assert results == []


def test_head_larger_than_input_returns_all():
    results = run_counter(SAMPLE, enabled=True, max_lines=100)
    assert len(results) == 10
