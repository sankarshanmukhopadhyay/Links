import base64
from nacl.signing import SigningKey

from links.policy_updates import build_update, sign_update_legacy, verify_update_any, compute_policy_hash


def test_policy_update_sign_verify():
    policy = {"visibility":"village","allowed_predicates":["links.weighted_to"],"max_window_days":30,"min_signature_alg":"Ed25519"}
    u = build_update("ops", policy, actor="alice")
    assert u.policy_hash == compute_policy_hash(policy)

    sk = SigningKey.generate()
    s = sign_update_legacy(u, sk)
    assert verify_update_any(s) is True

    # tamper
    t = s.model_copy(deep=True)
    t.policy["max_window_days"] = 999
    assert verify_update_any(t) is False
