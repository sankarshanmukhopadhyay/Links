import json
from nacl.signing import SigningKey

from links.claims import build_bundle_from_edges, sign_bundle, verify_bundle


def test_sign_verify_bundle(tmp_path):
    edges = [
        {"from_entity_id":"wikipedia:en:Alice","to_entity_id":"wikipedia:en:Bob","weight":1.0,"window_days":30,"derivation":"log(1 + count_30d)"},
        {"from_entity_id":"wikipedia:en:Bob","to_entity_id":"wikipedia:en:Alice","weight":0.7,"window_days":30,"derivation":"log(1 + count_30d)"},
    ]
    edges_path = tmp_path / "edges.json"
    edges_path.write_text(json.dumps(edges), encoding="utf-8")

    bundle = build_bundle_from_edges(edges_path, issuer="test-node", window_days=30)
    sk = SigningKey.generate()
    signed = sign_bundle(bundle, sk)
    assert verify_bundle(signed) is True

    tampered = signed.model_copy(deep=True)
    tampered.claims[0].value = 999
    assert verify_bundle(tampered) is False
