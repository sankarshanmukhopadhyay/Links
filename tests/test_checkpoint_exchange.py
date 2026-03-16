"""Tests for links.checkpoint_exchange."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from nacl.signing import SigningKey

from links.checkpoint_exchange import (
    CheckpointComparisonReport,
    compare_checkpoints,
    load_checkpoint_file,
    publish_checkpoint_file,
    sign_checkpoint,
    verify_checkpoint_signature,
    write_comparison_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_checkpoint(
    village_id: str = "ops",
    policy_hash: str = "abc123",
    entry_count: int = 5,
    checkpoint_hash: str = "deadbeef",
) -> dict:
    return {
        "village_id": village_id,
        "generated_at": "2026-03-14T10:00:00Z",
        "entry_count": entry_count,
        "latest_policy_hash": policy_hash,
        "checkpoint_hash": checkpoint_hash,
    }


# ---------------------------------------------------------------------------
# sign / verify
# ---------------------------------------------------------------------------


def test_sign_checkpoint_adds_signature():
    sk = SigningKey.generate()
    ckpt = _make_checkpoint()
    signed = sign_checkpoint(ckpt, sk)
    assert "signature" in signed
    assert "signer_key_hash" in signed
    # Original fields preserved
    assert signed["village_id"] == "ops"
    assert signed["entry_count"] == 5


def test_verify_checkpoint_signature_valid():
    sk = SigningKey.generate()
    ckpt = _make_checkpoint()
    signed = sign_checkpoint(ckpt, sk)
    ok, msg = verify_checkpoint_signature(signed, sk.verify_key)
    assert ok is True
    assert msg == "ok"


def test_verify_checkpoint_signature_tampered():
    sk = SigningKey.generate()
    ckpt = _make_checkpoint()
    signed = sign_checkpoint(ckpt, sk)
    signed["entry_count"] = 999  # tamper
    ok, msg = verify_checkpoint_signature(signed, sk.verify_key)
    assert ok is False


def test_verify_checkpoint_signature_missing():
    ckpt = _make_checkpoint()
    ok, msg = verify_checkpoint_signature(ckpt, SigningKey.generate().verify_key)
    assert ok is False
    assert "no signature" in msg


def test_sign_idempotent_re_sign():
    """Re-signing should not stack signatures."""
    sk = SigningKey.generate()
    ckpt = _make_checkpoint()
    signed1 = sign_checkpoint(ckpt, sk)
    signed2 = sign_checkpoint(signed1, sk)  # re-sign strips old sig
    ok, msg = verify_checkpoint_signature(signed2, sk.verify_key)
    assert ok is True


# ---------------------------------------------------------------------------
# publish / load
# ---------------------------------------------------------------------------


def test_publish_checkpoint_file_writes_json(tmp_path):
    ckpt = _make_checkpoint()
    path = publish_checkpoint_file(ckpt, tmp_path / "trans" / "ops", stamp="20260314T120000Z")
    assert path.exists()
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["village_id"] == "ops"


def test_publish_checkpoint_file_creates_dirs(tmp_path):
    ckpt = _make_checkpoint()
    out_dir = tmp_path / "a" / "b" / "c"
    path = publish_checkpoint_file(ckpt, out_dir)
    assert path.exists()


def test_publish_checkpoint_file_name_contains_village_id(tmp_path):
    ckpt = _make_checkpoint(village_id="finance")
    path = publish_checkpoint_file(ckpt, tmp_path, stamp="20260314T120000Z")
    assert "finance" in path.name


def test_load_checkpoint_file_roundtrip(tmp_path):
    sk = SigningKey.generate()
    ckpt = _make_checkpoint()
    signed = sign_checkpoint(ckpt, sk)
    path = publish_checkpoint_file(signed, tmp_path, stamp="T1")
    loaded = load_checkpoint_file(path)
    assert loaded["signature"] == signed["signature"]


# ---------------------------------------------------------------------------
# compare_checkpoints
# ---------------------------------------------------------------------------


def test_compare_aligned():
    local = _make_checkpoint(policy_hash="abc", entry_count=10, checkpoint_hash="h1")
    peer = _make_checkpoint(policy_hash="abc", entry_count=10, checkpoint_hash="h1")
    report = compare_checkpoints(local, peer)
    assert report.status == "aligned"
    assert report.drift_class == "aligned"


def test_compare_publication_lag():
    local = _make_checkpoint(policy_hash="abc", entry_count=10)
    peer = _make_checkpoint(policy_hash="abc", entry_count=8)
    report = compare_checkpoints(local, peer)
    assert report.drift_class == "publication_lag"
    assert report.status == "drift"


def test_compare_policy_divergence():
    local = _make_checkpoint(policy_hash="abc", entry_count=10)
    peer = _make_checkpoint(policy_hash="xyz", entry_count=10)
    report = compare_checkpoints(local, peer)
    assert report.drift_class == "policy_divergence"
    assert report.status == "drift"


def test_compare_report_fields():
    local = _make_checkpoint(village_id="ops", policy_hash="aaa", entry_count=5, checkpoint_hash="h1")
    peer = _make_checkpoint(village_id="ops", policy_hash="bbb", entry_count=6, checkpoint_hash="h2")
    report = compare_checkpoints(local, peer)
    assert report.village_id == "ops"
    assert report.local_entry_count == 5
    assert report.peer_entry_count == 6
    assert report.local_latest_policy_hash == "aaa"
    assert report.peer_latest_policy_hash == "bbb"
    assert isinstance(report.notes, list)
    assert len(report.notes) > 0


def test_compare_as_dict_has_all_keys():
    local = _make_checkpoint()
    peer = _make_checkpoint()
    report = compare_checkpoints(local, peer)
    d = report.as_dict()
    for key in (
        "village_id", "compared_at", "local_checkpoint_hash", "peer_checkpoint_hash",
        "local_entry_count", "peer_entry_count", "local_latest_policy_hash",
        "peer_latest_policy_hash", "drift_class", "status", "notes",
    ):
        assert key in d, f"missing key: {key}"


# ---------------------------------------------------------------------------
# write_comparison_report
# ---------------------------------------------------------------------------


def test_write_comparison_report(tmp_path):
    local = _make_checkpoint(policy_hash="abc", entry_count=10)
    peer = _make_checkpoint(policy_hash="xyz", entry_count=9)
    report = compare_checkpoints(local, peer)
    path = write_comparison_report(report, tmp_path / "reports", stamp="20260314T120000Z")
    assert path.exists()
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["drift_class"] == "policy_divergence"
    assert content["village_id"] == "ops"


def test_write_comparison_report_creates_dirs(tmp_path):
    local = _make_checkpoint()
    peer = _make_checkpoint()
    report = compare_checkpoints(local, peer)
    path = write_comparison_report(report, tmp_path / "deep" / "path", stamp="T1")
    assert path.exists()
