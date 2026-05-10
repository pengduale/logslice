import time
import pytest
from logslice.ratelimiter import RateLimiterConfig, LogRateLimiter


def make_limiter(enabled=True, max_lines_per_second=5.0, window_seconds=1.0):
    config = RateLimiterConfig(
        enabled=enabled,
        max_lines_per_second=max_lines_per_second,
        window_seconds=window_seconds,
    )
    return LogRateLimiter(config)


def test_invalid_rate_raises():
    with pytest.raises(ValueError, match="max_lines_per_second"):
        RateLimiterConfig(enabled=True, max_lines_per_second=0)


def test_invalid_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        RateLimiterConfig(enabled=True, window_seconds=-1.0)


def test_disabled_passes_all_lines():
    limiter = make_limiter(enabled=False, max_lines_per_second=1.0)
    for i in range(20):
        result = limiter.process(f"line {i}")
        assert result == f"line {i}"
    assert limiter.passed == 20
    assert limiter.dropped == 0


def test_within_limit_passes_lines():
    limiter = make_limiter(max_lines_per_second=10.0, window_seconds=1.0)
    results = [limiter.process(f"line {i}") for i in range(10)]
    assert all(r is not None for r in results)
    assert limiter.passed == 10
    assert limiter.dropped == 0


def test_exceeding_limit_drops_lines():
    limiter = make_limiter(max_lines_per_second=3.0, window_seconds=1.0)
    results = [limiter.process(f"line {i}") for i in range(6)]
    passed = [r for r in results if r is not None]
    dropped = [r for r in results if r is None]
    assert len(passed) == 3
    assert len(dropped) == 3
    assert limiter.passed == 3
    assert limiter.dropped == 3


def test_counters_start_at_zero():
    limiter = make_limiter()
    assert limiter.passed == 0
    assert limiter.dropped == 0


def test_line_content_preserved():
    limiter = make_limiter(max_lines_per_second=100.0)
    line = "ERROR something went wrong"
    assert limiter.process(line) == line


def test_config_accessible():
    config = RateLimiterConfig(enabled=True, max_lines_per_second=50.0)
    limiter = LogRateLimiter(config)
    assert limiter.config is config


def test_default_config_is_disabled():
    limiter = LogRateLimiter()
    assert limiter.config.enabled is False


def test_lines_pass_after_window_expires():
    limiter = make_limiter(max_lines_per_second=2.0, window_seconds=0.1)
    # Fill the window
    for i in range(2):
        limiter.process(f"line {i}")
    # Next line should be dropped
    assert limiter.process("overflow") is None
    # Wait for the window to expire
    time.sleep(0.15)
    # Now it should pass again
    assert limiter.process("after wait") is not None
