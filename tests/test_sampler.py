"""Tests for logslice.sampler."""

import pytest

from logslice.sampler import LogSampler, SamplerConfig


def make_sampler(enabled: bool = True, rate: int = 1, max_lines=None) -> LogSampler:
    return LogSampler(SamplerConfig(enabled=enabled, rate=rate, max_lines=max_lines))


# ---------------------------------------------------------------------------
# SamplerConfig validation
# ---------------------------------------------------------------------------

def test_invalid_rate_raises():
    with pytest.raises(ValueError, match="rate must be >= 1"):
        SamplerConfig(rate=0)


def test_invalid_max_lines_raises():
    with pytest.raises(ValueError, match="max_lines must be >= 1"):
        SamplerConfig(max_lines=0)


# ---------------------------------------------------------------------------
# Disabled sampler
# ---------------------------------------------------------------------------

def test_disabled_passes_all_lines():
    sampler = make_sampler(enabled=False)
    lines = ["line1", "line2", "line3"]
    result = [sampler.process(l) for l in lines]
    assert result == lines


def test_disabled_counters_stay_zero():
    sampler = make_sampler(enabled=False)
    for _ in range(5):
        sampler.process("x")
    assert sampler.seen == 0
    assert sampler.emitted == 0


# ---------------------------------------------------------------------------
# Rate sampling
# ---------------------------------------------------------------------------

def test_rate_1_passes_every_line():
    sampler = make_sampler(rate=1)
    results = [sampler.process(f"line{i}") for i in range(4)]
    assert all(r is not None for r in results)


def test_rate_2_passes_every_other_line():
    sampler = make_sampler(rate=2)
    results = [sampler.process(f"line{i}") for i in range(6)]
    # seen counts: 1,2,3,4,5,6 — emit when seen % 2 == 0
    assert results == [None, "line1", None, "line3", None, "line5"]


def test_rate_3_passes_every_third_line():
    sampler = make_sampler(rate=3)
    results = [sampler.process(f"L{i}") for i in range(9)]
    emitted = [r for r in results if r is not None]
    assert len(emitted) == 3
    assert emitted == ["L2", "L5", "L8"]


def test_seen_counter_increments_on_every_call():
    sampler = make_sampler(rate=3)
    for _ in range(7):
        sampler.process("x")
    assert sampler.seen == 7


def test_emitted_counter_reflects_passed_lines():
    sampler = make_sampler(rate=2)
    for _ in range(6):
        sampler.process("x")
    assert sampler.emitted == 3


# ---------------------------------------------------------------------------
# max_lines cap
# ---------------------------------------------------------------------------

def test_max_lines_stops_emission_after_cap():
    sampler = make_sampler(rate=1, max_lines=3)
    results = [sampler.process(f"L{i}") for i in range(6)]
    emitted = [r for r in results if r is not None]
    assert len(emitted) == 3
    assert emitted == ["L0", "L1", "L2"]


def test_max_lines_with_rate_combined():
    sampler = make_sampler(rate=2, max_lines=2)
    results = [sampler.process(f"L{i}") for i in range(8)]
    emitted = [r for r in results if r is not None]
    assert len(emitted) == 2


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def test_summary_contains_key_fields():
    sampler = make_sampler(rate=2)
    for _ in range(4):
        sampler.process("x")
    summary = sampler.summary()
    assert "seen=4" in summary
    assert "emitted=2" in summary
    assert "suppressed=2" in summary
    assert "rate=1/2" in summary
