import json
from pathlib import Path
from datetime import datetime, timezone
from nacl.signing import SigningKey

from links.claims import build_bundle_from_edges, sign_bundle
from links.villages import Village, VillageGovernance, VillagePolicy, save_village, add_member, issuer_key_hash_from_public_key_b64, add_issuer_allow, issuer_allowed


def test_issuer_allowlist_policy(tmp_path):
    data_root = tmp_path / "data"
    (data_root / "villages").mkdir(parents=True, exist_ok=True)

    v = Village(
        village_id="ops",
        name="Ops",
        description="",
        created_at=datetime.now(timezone.utc),
        governance=VillageGovernance(admins=["alice"]),
        policy=VillagePolicy(require_issuer_allowlist=True),
    )
    save_village(data_root, v)

    sk = SigningKey.generate()
    pub_b64 = __import__("base64").b64encode(sk.verify_key.encode()).decode("utf-8")
    kh = issuer_key_hash_from_public_key_b64(pub_b64)

    # not allowed before allow
    v2 = Village.model_validate_json((data_root/"villages"/"ops"/"village.json").read_text(encoding="utf-8"))
    assert issuer_allowed(v2.policy, kh) is False

    add_issuer_allow(data_root, "ops", kh, actor="alice")
    v3 = Village.model_validate_json((data_root/"villages"/"ops"/"village.json").read_text(encoding="utf-8"))
    assert issuer_allowed(v3.policy, kh) is True
