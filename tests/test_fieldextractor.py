"""Tests for logslice.fieldextractor."""
import pytest

from logslice.fieldextractor import (
    ExtractionResult,
    FieldExtractorConfig,
    LogFieldExtractor,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_extractor(patterns=None, enabled=True) -> LogFieldExtractor:
    cfg = FieldExtractorConfig(enabled=enabled, patterns=patterns or [])
    return LogFieldExtractor(cfg)


# ---------------------------------------------------------------------------
# config validation
# ---------------------------------------------------------------------------

def test_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid pattern"):
        FieldExtractorConfig(enabled=True, patterns=["(unclosed"])


def test_pattern_without_named_groups_raises():
    with pytest.raises(ValueError, match="no named groups"):
        FieldExtractorConfig(enabled=True, patterns=[r"(\d+)"])


def test_valid_pattern_does_not_raise():
    cfg = FieldExtractorConfig(
        enabled=True, patterns=[r"(?P<level>\w+)"]
    )
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# disabled extractor
# ---------------------------------------------------------------------------

def test_disabled_extract_returns_no_match():
    ext = make_extractor(patterns=[r"(?P<level>\w+)"], enabled=False)
    result = ext.extract("ERROR something happened")
    assert result.matched is False
    assert result.fields == {}


def test_disabled_extract_all_returns_empty_list():
    ext = make_extractor(patterns=[r"(?P<level>\w+)"], enabled=False)
    assert ext.extract_all("ERROR something") == []


# ---------------------------------------------------------------------------
# extract (first match wins)
# ---------------------------------------------------------------------------

def test_extract_returns_named_fields():
    ext = make_extractor(patterns=[r"(?P<level>\w+)\s+(?P<msg>.+)"])
    result = ext.extract("ERROR disk full")
    assert result.matched is True
    assert result.fields["level"] == "ERROR"
    assert result.fields["msg"] == "disk full"


def test_extract_no_match_returns_empty():
    ext = make_extractor(patterns=[r"(?P<ts>\d{4}-\d{2}-\d{2})"])
    result = ext.extract("no date here")
    assert result.matched is False
    assert result.fields == {}


def test_extract_first_matching_pattern_wins():
    ext = make_extractor(
        patterns=[
            r"(?P<level>ERROR|WARN)",
            r"(?P<level>INFO|DEBUG)",
        ]
    )
    result = ext.extract("INFO startup")
    # first pattern does not match; second should win
    assert result.matched is True
    assert result.fields["level"] == "INFO"
    assert result.pattern is not None and "INFO" in result.pattern


def test_extract_stores_matching_pattern():
    pat = r"(?P<code>\d{3})"
    ext = make_extractor(patterns=[pat])
    result = ext.extract("status 404 not found")
    assert result.pattern == pat


# ---------------------------------------------------------------------------
# extract_all (all matches)
# ---------------------------------------------------------------------------

def test_extract_all_returns_all_matching_patterns():
    ext = make_extractor(
        patterns=[
            r"(?P<level>\w+)",
            r"(?P<code>\d+)",
        ]
    )
    results = ext.extract_all("ERROR 500 internal")
    assert len(results) == 2
    assert results[0].fields.get("level") == "ERROR"
    assert results[1].fields.get("code") == "500"


def test_extract_all_skips_non_matching_patterns():
    ext = make_extractor(
        patterns=[
            r"(?P<ts>\d{4}-\d{2}-\d{2})",
            r"(?P<code>\d{3})",
        ]
    )
    results = ext.extract_all("status 200 OK")
    assert len(results) == 1
    assert results[0].fields["code"] == "200"


def test_extract_all_empty_when_nothing_matches():
    ext = make_extractor(patterns=[r"(?P<ts>\d{4}-\d{2}-\d{2})"])
    assert ext.extract_all("no date") == []
