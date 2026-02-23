from datetime import datetime, timezone
from pathlib import Path

from links.villages import Village, VillageGovernance, VillagePolicy, save_village, add_member, authorize


def test_village_token_auth(tmp_path):
    data_root = tmp_path / "data"
    (data_root / "villages").mkdir(parents=True, exist_ok=True)

    v = Village(
        village_id="test",
        name="Test",
        description="",
        created_at=datetime.now(timezone.utc),
        governance=VillageGovernance(admins=["admin"]),
        policy=VillagePolicy(),
    )
    save_village(data_root, v)
    token = "secret-token"
    add_member(data_root, "test", "alice", "member", token_plain=token)
    assert authorize(data_root, "test", token) is not None
    assert authorize(data_root, "test", "wrong") is None
