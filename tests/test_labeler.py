import re  # noqa: E402 – needed for the exception type above
import pytest
from logslice.labeler import LabelRule, LabelerConfig, LogLabeler


def make_labeler(
    rules=None,
    enabled=True,
    default_label=None,
) -> LogLabeler:
    cfg = LabelerConfig(
        rules=rules or [],
        enabled=enabled,
        default_label=default_label,
    )
    return LogLabeler(cfg)


# ---------------------------------------------------------------------------
# LabelRule
# ---------------------------------------------------------------------------

def test_label_rule_matches_pattern():
    rule = LabelRule(pattern=r"ERROR", label="error")
    assert rule.matches("2024-01-01 ERROR something broke")


def test_label_rule_no_match_returns_false():
    rule = LabelRule(pattern=r"ERROR", label="error")
    assert not rule.matches("INFO everything is fine")


def test_label_rule_invalid_pattern_raises():
    with pytest.raises(re.error):
        LabelRule(pattern=r"[", label="bad")


# ---------------------------------------------------------------------------
# LogLabeler.label_line
# ---------------------------------------------------------------------------

def test_disabled_returns_none_without_default():
    labeler = make_labeler(rules=[LabelRule(r"ERROR", "error")], enabled=False)
    assert labeler.label_line("ERROR boom") is None


def test_disabled_returns_default_label():
    labeler = make_labeler(
        rules=[LabelRule(r"ERROR", "error")],
        enabled=False,
        default_label="unknown",
    )
    assert labeler.label_line("ERROR boom") == "unknown"


def test_first_matching_rule_wins():
    rules = [
        LabelRule(r"ERROR", "error"),
        LabelRule(r"ERR", "err-generic"),
    ]
    labeler = make_labeler(rules=rules)
    assert labeler.label_line("ERROR critical") == "error"


def test_no_match_returns_default():
    labeler = make_labeler(
        rules=[LabelRule(r"ERROR", "error")],
        default_label="info",
    )
    assert labeler.label_line("INFO all good") == "info"


def test_no_match_no_default_returns_none():
    labeler = make_labeler(rules=[LabelRule(r"ERROR", "error")])
    assert labeler.label_line("DEBUG verbose") is None


def test_no_rules_returns_default():
    labeler = make_labeler(default_label="general")
    assert labeler.label_line("anything here") == "general"


# ---------------------------------------------------------------------------
# LogLabeler.annotate
# ---------------------------------------------------------------------------

def test_annotate_prefixes_label():
    labeler = make_labeler(rules=[LabelRule(r"WARN", "warning")])
    result = labeler.annotate("WARN disk almost full")
    assert result == "[warning] WARN disk almost full"


def test_annotate_no_label_returns_line_unchanged():
    labeler = make_labeler()
    line = "DEBUG nothing special"
    assert labeler.annotate(line) == line


def test_annotate_empty_line_returns_empty():
    """An empty line with no matching rules and no default should be returned unchanged."""
    labeler = make_labeler(rules=[LabelRule(r"ERROR", "error")])
    assert labeler.annotate("") == ""


def test_annotate_empty_line_with_default_label():
    """An empty line should still receive a label prefix when a default label is set."""
    labeler = make_labeler(default_label="general")
    assert labeler.annotate("") == "[general] "


def test_config_property_returns_config():
    labeler = make_labeler(default_label="default")
    assert labeler.config.default_label == "default"
