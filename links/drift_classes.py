"""drift_classes — drift class taxonomy for federation comparison workflows.

Background
----------
When two PolicyMesh nodes compare transparency checkpoints, not all differences
indicate a governance failure.  A peer node might simply be behind in its
publication of transparency entries even though its policy is fully aligned.
Without distinguishing these cases, operators cannot assess severity or choose
an appropriate response.

This module provides a formal taxonomy of drift classes and a classifier
function that assigns an observed checkpoint difference to one of them.

Drift class taxonomy
--------------------

aligned
    Local and peer agree on policy hash *and* entry count.  No action needed.

publication_lag
    Policy hashes match but entry counts differ.  The peer has the same policy
    but has not yet published (or the local node has not yet received) all
    transparency entries.  This is a temporary and expected state; no policy
    action is required.  Operators may re-check after the peer's next
    publication cycle.

policy_divergence
    Policy hashes differ.  The two nodes have genuinely different current
    policies.  This requires operator investigation: determine which head is
    authoritative, reconcile lineage, and apply a corrective update if
    necessary.

history_only_divergence
    Policy hashes match and entry counts match, but the checkpoint hashes
    differ.  This is unusual and may indicate hash computation differences or
    a corrupted artifact.  Operators should verify checkpoint generation logic.

unknown
    Insufficient data to classify (e.g. missing required fields).

Typical usage
-------------
    from links.drift_classes import classify_checkpoint_drift, DRIFT_CLASS_DESCRIPTIONS

    drift_class, notes = classify_checkpoint_drift(
        local_policy_hash="abc123",
        peer_policy_hash="def456",
        local_entry_count=10,
        peer_entry_count=10,
    )
    # drift_class == "policy_divergence"
    print(DRIFT_CLASS_DESCRIPTIONS[drift_class])
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------

DRIFT_CLASSES = (
    "aligned",
    "publication_lag",
    "policy_divergence",
    "history_only_divergence",
    "unknown",
)

DRIFT_CLASS_DESCRIPTIONS: dict[str, str] = {
    "aligned": (
        "Both nodes share the same current policy hash and publication state. "
        "No action required."
    ),
    "publication_lag": (
        "Policy hashes agree but entry counts differ. The peer is behind in "
        "publishing transparency entries. No policy action needed; re-check "
        "after the peer's next publication cycle."
    ),
    "policy_divergence": (
        "Policy hashes differ. The nodes hold different current policies. "
        "Operator investigation is required: identify the authoritative head, "
        "reconcile lineage, and apply a corrective update if necessary."
    ),
    "history_only_divergence": (
        "Policy hashes and entry counts match but checkpoint hashes differ. "
        "This may indicate a checkpoint computation inconsistency or artifact "
        "corruption. Verify checkpoint generation logic on both nodes."
    ),
    "unknown": (
        "Insufficient data to classify the drift. Check that both checkpoint "
        "artifacts contain required fields (latest_policy_hash, entry_count, "
        "checkpoint_hash)."
    ),
}

# Severity ordering for programmatic comparisons (higher = more severe)
DRIFT_CLASS_SEVERITY: dict[str, int] = {
    "aligned": 0,
    "publication_lag": 1,
    "history_only_divergence": 2,
    "policy_divergence": 3,
    "unknown": 1,
}

# Response guidance keyed by drift class
DRIFT_CLASS_OPERATOR_RESPONSE: dict[str, str] = {
    "aligned": "No action required.",
    "publication_lag": (
        "Wait for the peer's next publication cycle and re-run the comparison. "
        "If lag persists beyond expected publication intervals, investigate "
        "whether the peer's transparency pipeline is healthy."
    ),
    "policy_divergence": (
        "1. Run `links policy reconcile` to compare local and remote update chains. "
        "2. Identify the authoritative governance branch. "
        "3. Verify signer allowlist constraints. "
        "4. Apply a corrective policy update referencing the desired parent hash. "
        "5. Archive the rejected branch in incident records."
    ),
    "history_only_divergence": (
        "1. Re-generate the transparency checkpoint on both nodes. "
        "2. Verify that both nodes use the same checkpoint generation code version. "
        "3. If hashes still differ, examine the underlying transparency entry logs."
    ),
    "unknown": (
        "Inspect both checkpoint artifacts for missing fields and re-run the "
        "comparison once both artifacts contain complete data."
    ),
}


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


def classify_checkpoint_drift(
    *,
    local_policy_hash: str,
    peer_policy_hash: str,
    local_entry_count: int,
    peer_entry_count: int,
    local_checkpoint_hash: str = "",
    peer_checkpoint_hash: str = "",
) -> tuple[str, list[str]]:
    """Classify the drift between two checkpoint observations.

    Parameters
    ----------
    local_policy_hash, peer_policy_hash:
        The ``latest_policy_hash`` fields from the respective checkpoints.
    local_entry_count, peer_entry_count:
        The ``entry_count`` fields from the respective checkpoints.
    local_checkpoint_hash, peer_checkpoint_hash:
        Optional ``checkpoint_hash`` fields for finer-grained classification.

    Returns
    -------
    (drift_class, notes)
        *drift_class* is one of the :data:`DRIFT_CLASSES` strings.
        *notes* is a list of human-readable diagnostic strings.
    """
    notes: list[str] = []

    # Guard: missing required data
    if not local_policy_hash or not peer_policy_hash:
        notes.append("One or both policy hashes are empty; cannot classify.")
        return "unknown", notes

    policy_match = local_policy_hash == peer_policy_hash
    count_match = local_entry_count == peer_entry_count

    if policy_match and count_match:
        # Check checkpoint hash if provided for extra fidelity
        if (
            local_checkpoint_hash
            and peer_checkpoint_hash
            and local_checkpoint_hash != peer_checkpoint_hash
        ):
            notes.append(
                f"Policy hash and entry count agree but checkpoint hashes differ: "
                f"local={local_checkpoint_hash!r}, peer={peer_checkpoint_hash!r}."
            )
            return "history_only_divergence", notes
        return "aligned", notes

    if policy_match and not count_match:
        lag = peer_entry_count - local_entry_count
        direction = "peer is ahead by" if lag > 0 else "local is ahead by"
        notes.append(
            f"Policy hashes agree. Entry count differs ({direction} {abs(lag)} entries). "
            f"local_count={local_entry_count}, peer_count={peer_entry_count}."
        )
        return "publication_lag", notes

    # Policy hashes differ
    notes.append(
        f"Policy hash mismatch: local={local_policy_hash!r}, peer={peer_policy_hash!r}."
    )
    if not count_match:
        notes.append(
            f"Entry counts also differ: local={local_entry_count}, peer={peer_entry_count}."
        )
    notes.append(DRIFT_CLASS_OPERATOR_RESPONSE["policy_divergence"])
    return "policy_divergence", notes


# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------


def drift_severity(drift_class: str) -> int:
    """Return the integer severity score for *drift_class*.

    Higher values indicate more operator attention required.
    Unknown classes return 1 (same as ``"unknown"`` and ``"publication_lag"``).
    """
    return DRIFT_CLASS_SEVERITY.get(drift_class, 1)


def most_severe(drift_classes: list[str]) -> str:
    """Return the most severe drift class from *drift_classes*.

    If the list is empty, returns ``"unknown"``.
    """
    if not drift_classes:
        return "unknown"
    return max(drift_classes, key=drift_severity)
