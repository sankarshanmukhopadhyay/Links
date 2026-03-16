"""Tests for links.capability_manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from links.capability_manifest import (
    EXPERIMENTAL_FEATURES,
    MANIFEST_SCHEMA_VERSION,
    STABLE_FEATURES,
    build_manifest,
    check_compatibility,
    load_manifest,
    verify_manifest_hash,
    write_manifest,
)


# ---------------------------------------------------------------------------
# build_manifest
# ---------------------------------------------------------------------------


def test_build_manifest_minimal():
    m = build_manifest(node_id="node.example.org")
    assert m["node_id"] == "node.example.org"
    assert m["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert "generated_at" in m
    assert m["storage_mode"] == "filesystem"
    assert m["reconciliation_mode"] == "lineage_aware"
    assert isinstance(m["stable_features"], list)
    assert isinstance(m["experimental_features"], list)
    assert isinstance(m["transparency_features"], list)
    assert m["federation_pilot"] is False
    assert "manifest_hash" in m


def test_build_manifest_sqlite_mode():
    m = build_manifest(node_id="n1", storage_mode="sqlite")
    assert m["storage_mode"] == "sqlite"
    assert "storage_sqlite" in m["stable_features"]


def test_build_manifest_invalid_storage_mode():
    with pytest.raises(ValueError, match="storage_mode"):
        build_manifest(node_id="n", storage_mode="postgres")


def test_build_manifest_invalid_reconciliation_mode():
    with pytest.raises(ValueError, match="reconciliation_mode"):
        build_manifest(node_id="n", reconciliation_mode="random")


def test_build_manifest_with_transparency_features():
    m = build_manifest(
        node_id="n",
        transparency_features=["http_publish", "signed_checkpoint"],
    )
    assert "http_publish" in m["transparency_features"]
    assert "signed_checkpoint" in m["transparency_features"]
    assert m["transparency_features"] == sorted(m["transparency_features"])


def test_build_manifest_with_experimental():
    m = build_manifest(
        node_id="n",
        experimental_features=["checkpoint_peer_compare"],
    )
    assert "checkpoint_peer_compare" in m["experimental_features"]


def test_build_manifest_federation_pilot():
    m = build_manifest(node_id="n", federation_pilot=True)
    assert m["federation_pilot"] is True


def test_build_manifest_operator_notes():
    m = build_manifest(node_id="n", operator_notes="dev node")
    assert m["operator_notes"] == "dev node"


def test_build_manifest_extra_extensions():
    m = build_manifest(node_id="n", extra={"deployment": "k8s", "region": "ap-south-1"})
    assert m["extensions"]["deployment"] == "k8s"


# ---------------------------------------------------------------------------
# verify_manifest_hash
# ---------------------------------------------------------------------------


def test_verify_manifest_hash_ok():
    m = build_manifest(node_id="n")
    ok, msg = verify_manifest_hash(m)
    assert ok is True
    assert msg == "ok"


def test_verify_manifest_hash_tampered():
    m = build_manifest(node_id="n")
    m["node_id"] = "tampered"
    ok, msg = verify_manifest_hash(m)
    assert ok is False
    assert "mismatch" in msg


def test_verify_manifest_hash_missing():
    m = build_manifest(node_id="n")
    del m["manifest_hash"]
    ok, msg = verify_manifest_hash(m)
    assert ok is False
    assert "missing" in msg


# ---------------------------------------------------------------------------
# write / load round-trip
# ---------------------------------------------------------------------------


def test_write_load_roundtrip(tmp_path):
    m = build_manifest(node_id="roundtrip-node", transparency_features=["http_publish"])
    path = tmp_path / "manifest.json"
    written = write_manifest(path, m)
    assert written.exists()

    loaded = load_manifest(path)
    assert loaded["node_id"] == "roundtrip-node"
    ok, _ = verify_manifest_hash(loaded)
    assert ok is True


def test_write_creates_parent_dirs(tmp_path):
    m = build_manifest(node_id="n")
    nested = tmp_path / "deep" / "nested" / "manifest.json"
    write_manifest(nested, m)
    assert nested.exists()


def test_written_file_is_valid_json(tmp_path):
    m = build_manifest(node_id="n")
    path = tmp_path / "m.json"
    write_manifest(path, m)
    content = path.read_text(encoding="utf-8")
    parsed = json.loads(content)
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# check_compatibility
# ---------------------------------------------------------------------------


def test_compatible_identical_manifests():
    m1 = build_manifest(node_id="a")
    m2 = build_manifest(node_id="b")
    report = check_compatibility(m1, m2)
    assert report["compatible"] is True
    assert report["storage_match"] is True
    assert report["reconciliation_match"] is True


def test_incompatible_storage_when_required():
    m1 = build_manifest(node_id="a", storage_mode="filesystem")
    m2 = build_manifest(node_id="b", storage_mode="sqlite")
    report = check_compatibility(m1, m2, require_storage_match=True)
    assert report["compatible"] is False
    assert any("storage_mode" in n for n in report["notes"])


def test_compatible_storage_mismatch_not_required():
    m1 = build_manifest(node_id="a", storage_mode="filesystem")
    m2 = build_manifest(node_id="b", storage_mode="sqlite")
    report = check_compatibility(m1, m2, require_storage_match=False)
    # storage mismatch alone should not block compatibility
    assert report["compatible"] is True
    assert report["storage_match"] is False


def test_reconciliation_mismatch_produces_note():
    m1 = build_manifest(node_id="a", reconciliation_mode="lineage_aware")
    m2 = build_manifest(node_id="b", reconciliation_mode="latest_wins")
    report = check_compatibility(m1, m2)
    assert any("reconciliation_mode" in n for n in report["notes"])


def test_federation_pilot_note():
    m1 = build_manifest(node_id="a", federation_pilot=False)
    m2 = build_manifest(node_id="b", federation_pilot=True)
    report = check_compatibility(m1, m2)
    assert any("federation_pilot" in n for n in report["notes"])


def test_shared_and_exclusive_features():
    m1 = build_manifest(node_id="a", storage_mode="filesystem")
    m2 = build_manifest(node_id="b", storage_mode="sqlite")
    report = check_compatibility(m1, m2)
    # Both have reconciliation_lineage_aware in stable
    assert "reconciliation_lineage_aware" in report["shared_stable_features"]
    # m1 has filesystem, m2 has sqlite — should appear in respective exclusive lists
    assert "storage_filesystem" in report["local_only_features"]
    assert "storage_sqlite" in report["peer_only_features"]
