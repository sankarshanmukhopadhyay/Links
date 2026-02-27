from __future__ import annotations

from datetime import datetime, timezone, timedelta

from links.policy_updates import build_update, verify_update_any


def test_policy_update_has_lifecycle_and_quorum_metadata():
    u = build_update(
        village_id="demo",
        actor="tester",
        policy={"visibility":"village","rate_limit_per_min":10},
        lifecycle_state="proposal",
        quorum_metadata={"model":"m_of_n","threshold_m":1},
        change_summary={"added":["/foo"],"removed":[],"changed":[]},
        policy_version_id="v1",
        activation_time="2026-01-01T00:00:00Z",
    )
    assert u.lifecycle_state in {"proposal","approved","active"}
    assert u.quorum_metadata is not None
    assert u.policy_version_id == "v1"


def test_policy_update_expiry_field_roundtrip():
    # expiry is optional; presence should not break validation
    u = build_update(
        village_id="demo",
        actor="tester",
        policy={"visibility":"village"},
        lifecycle_state="proposal",
    )
    assert u.expires_at is None
