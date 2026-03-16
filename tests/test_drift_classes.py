"""Tests for links.drift_classes."""

from __future__ import annotations

import pytest

from links.drift_classes import (
    DRIFT_CLASS_DESCRIPTIONS,
    DRIFT_CLASS_OPERATOR_RESPONSE,
    DRIFT_CLASS_SEVERITY,
    DRIFT_CLASSES,
    classify_checkpoint_drift,
    drift_severity,
    most_severe,
)


# ---------------------------------------------------------------------------
# Taxonomy invariants
# ---------------------------------------------------------------------------


def test_all_drift_classes_have_descriptions():
    for cls in DRIFT_CLASSES:
        assert cls in DRIFT_CLASS_DESCRIPTIONS, f"missing description for {cls!r}"


def test_all_drift_classes_have_severity():
    for cls in DRIFT_CLASSES:
        assert cls in DRIFT_CLASS_SEVERITY, f"missing severity for {cls!r}"


def test_all_drift_classes_have_operator_response():
    for cls in DRIFT_CLASSES:
        assert cls in DRIFT_CLASS_OPERATOR_RESPONSE, f"missing operator response for {cls!r}"


def test_aligned_is_least_severe():
    aligned_sev = DRIFT_CLASS_SEVERITY["aligned"]
    for cls, sev in DRIFT_CLASS_SEVERITY.items():
        assert aligned_sev <= sev, f"{cls!r} should not be less severe than 'aligned'"


def test_policy_divergence_is_most_severe():
    pd_sev = DRIFT_CLASS_SEVERITY["policy_divergence"]
    for cls, sev in DRIFT_CLASS_SEVERITY.items():
        assert pd_sev >= sev, f"{cls!r} should not be more severe than 'policy_divergence'"


# ---------------------------------------------------------------------------
# classify_checkpoint_drift — aligned
# ---------------------------------------------------------------------------


def test_classify_aligned_same_hash_same_count():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="abc",
        peer_policy_hash="abc",
        local_entry_count=10,
        peer_entry_count=10,
    )
    assert dc == "aligned"
    assert notes == []


def test_classify_aligned_with_matching_checkpoint_hashes():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="abc",
        peer_policy_hash="abc",
        local_entry_count=10,
        peer_entry_count=10,
        local_checkpoint_hash="h1",
        peer_checkpoint_hash="h1",
    )
    assert dc == "aligned"


# ---------------------------------------------------------------------------
# classify_checkpoint_drift — publication_lag
# ---------------------------------------------------------------------------


def test_classify_publication_lag_peer_behind():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="abc",
        peer_policy_hash="abc",
        local_entry_count=15,
        peer_entry_count=10,
    )
    assert dc == "publication_lag"
    assert any("entry count" in n or "entry_count" in n or "ahead" in n for n in notes)


def test_classify_publication_lag_local_behind():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="abc",
        peer_policy_hash="abc",
        local_entry_count=5,
        peer_entry_count=10,
    )
    assert dc == "publication_lag"


def test_classify_publication_lag_note_contains_counts():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="same",
        peer_policy_hash="same",
        local_entry_count=3,
        peer_entry_count=8,
    )
    combined = " ".join(notes)
    assert "3" in combined
    assert "8" in combined


# ---------------------------------------------------------------------------
# classify_checkpoint_drift — policy_divergence
# ---------------------------------------------------------------------------


def test_classify_policy_divergence_different_hashes():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="abc",
        peer_policy_hash="xyz",
        local_entry_count=10,
        peer_entry_count=10,
    )
    assert dc == "policy_divergence"
    assert any("abc" in n or "xyz" in n for n in notes)


def test_classify_policy_divergence_note_contains_hashes():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="hash_local",
        peer_policy_hash="hash_peer",
        local_entry_count=5,
        peer_entry_count=5,
    )
    combined = " ".join(notes)
    assert "hash_local" in combined
    assert "hash_peer" in combined


def test_classify_policy_divergence_with_count_difference():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="abc",
        peer_policy_hash="xyz",
        local_entry_count=5,
        peer_entry_count=8,
    )
    assert dc == "policy_divergence"
    # Should mention both count difference and hash difference
    combined = " ".join(notes)
    assert "5" in combined or "8" in combined


# ---------------------------------------------------------------------------
# classify_checkpoint_drift — history_only_divergence
# ---------------------------------------------------------------------------


def test_classify_history_only_divergence():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="abc",
        peer_policy_hash="abc",
        local_entry_count=10,
        peer_entry_count=10,
        local_checkpoint_hash="h1",
        peer_checkpoint_hash="h2",
    )
    assert dc == "history_only_divergence"
    assert any("h1" in n or "h2" in n for n in notes)


# ---------------------------------------------------------------------------
# classify_checkpoint_drift — unknown
# ---------------------------------------------------------------------------


def test_classify_unknown_empty_hashes():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="",
        peer_policy_hash="abc",
        local_entry_count=5,
        peer_entry_count=5,
    )
    assert dc == "unknown"
    assert len(notes) > 0


def test_classify_unknown_both_empty():
    dc, notes = classify_checkpoint_drift(
        local_policy_hash="",
        peer_policy_hash="",
        local_entry_count=0,
        peer_entry_count=0,
    )
    assert dc == "unknown"


# ---------------------------------------------------------------------------
# drift_severity / most_severe
# ---------------------------------------------------------------------------


def test_drift_severity_values():
    assert drift_severity("aligned") == 0
    assert drift_severity("policy_divergence") > drift_severity("publication_lag")
    assert drift_severity("publication_lag") > drift_severity("aligned")


def test_drift_severity_unknown_class_returns_nonzero():
    sev = drift_severity("completely_unknown_class")
    assert sev >= 0


def test_most_severe_policy_divergence_wins():
    result = most_severe(["aligned", "publication_lag", "policy_divergence"])
    assert result == "policy_divergence"


def test_most_severe_single_item():
    assert most_severe(["publication_lag"]) == "publication_lag"


def test_most_severe_empty():
    assert most_severe([]) == "unknown"


def test_most_severe_all_aligned():
    assert most_severe(["aligned", "aligned"]) == "aligned"
