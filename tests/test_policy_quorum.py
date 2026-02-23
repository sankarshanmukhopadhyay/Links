import base64
from nacl.signing import SigningKey

from links.policy_updates import build_update, add_signature, verify_update_quorum, key_hash_from_public_key_b64


def test_quorum_m_of_n():
    policy = {"visibility":"village","allowed_predicates":["links.weighted_to"],"max_window_days":30}
    u = build_update("ops", policy, actor="alice")

    sk1 = SigningKey.generate()
    sk2 = SigningKey.generate()
    sk3 = SigningKey.generate()

    # allowlist: signer 1 and 2 only
    allow = [
        key_hash_from_public_key_b64(base64.b64encode(sk1.verify_key.encode()).decode("utf-8")),
        key_hash_from_public_key_b64(base64.b64encode(sk2.verify_key.encode()).decode("utf-8")),
    ]

    u1 = add_signature(u, sk1)
    ok, msg = verify_update_quorum(u1, required_m=2, signer_allowlist=allow)
    assert ok is False

    u2 = add_signature(u1, sk2)
    ok, msg = verify_update_quorum(u2, required_m=2, signer_allowlist=allow)
    assert ok is True

    # signer 3 is not allowlisted; should not help
    u3 = add_signature(u2, sk3)
    ok, msg = verify_update_quorum(u3, required_m=3, signer_allowlist=allow)
    assert ok is False
