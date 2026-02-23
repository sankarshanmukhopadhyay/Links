from datetime import datetime, timezone, timedelta
from pathlib import Path

from links.policy_updates import VillagePolicyUpdate, compute_policy_hash
from links.policy_feed import store_policy_update, latest_policy_update


def test_latest_policy_update(tmp_path):
    root = tmp_path
    v_id = "ops"
    p1 = {"a": 1}
    p2 = {"a": 2}
    u1 = VillagePolicyUpdate(village_id=v_id, created_at=datetime.now(timezone.utc)-timedelta(minutes=5), actor="a", policy=p1, policy_hash=compute_policy_hash(p1))
    u2 = VillagePolicyUpdate(village_id=v_id, created_at=datetime.now(timezone.utc), actor="b", policy=p2, policy_hash=compute_policy_hash(p2))
    store_policy_update(root, u1)
    store_policy_update(root, u2)
    latest = latest_policy_update(root, v_id)
    assert latest is not None
    assert latest.policy_hash == u2.policy_hash
