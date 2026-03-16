"""checkpoint_exchange — HTTP transparency checkpoint publication and peer comparison.

This module provides the operator-facing surface for:

1. Publishing a signed transparency checkpoint artifact over HTTP so that
   peers can retrieve and verify it without direct store access.
2. Fetching a peer's checkpoint from a remote PolicyMesh node.
3. Comparing a local checkpoint against a peer checkpoint to identify
   divergence and generate a structured comparison report.

Design notes
------------
- Checkpoint payloads are self-describing JSON blobs with an optional
  Ed25519 signature embedded as a ``signature`` field (hex-encoded).
- Comparisons produce a ``CheckpointComparisonReport`` that distinguishes
  *policy divergence* from *publication lag*; see ``drift_classes`` for
  the full taxonomy.
- No server-side state is mutated here; this module is a pure client/tool
  surface.  The server endpoint is registered separately in ``server.py``.

Typical usage
-------------
    from nacl.signing import SigningKey
    from links.checkpoint_exchange import (
        sign_checkpoint,
        publish_checkpoint_file,
        fetch_peer_checkpoint,
        compare_checkpoints,
    )

    sk = SigningKey.generate()
    artifact = sign_checkpoint(raw_checkpoint, sk)
    publish_checkpoint_file(artifact, out_dir=Path("artifacts/transparency/ops"))

    peer_artifact = fetch_peer_checkpoint("https://peer.example.org", "ops")
    report = compare_checkpoints(artifact, peer_artifact)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Optional nacl import – signing is opt-in
try:
    from nacl.signing import SigningKey as _SigningKey  # type: ignore
    _NACL_AVAILABLE = True
except ImportError:
    _NACL_AVAILABLE = False

# Optional requests import – fetching is opt-in
try:
    import requests as _requests  # type: ignore
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def sign_checkpoint(
    checkpoint: dict[str, Any],
    signing_key: Any,  # nacl.signing.SigningKey
) -> dict[str, Any]:
    """Return a copy of *checkpoint* with an embedded Ed25519 signature.

    The signature covers the canonical JSON of all fields *except*
    ``signature`` (so callers can safely re-sign without stripping first).

    Parameters
    ----------
    checkpoint:
        A checkpoint dict as returned by ``links.transparency``.
    signing_key:
        A ``nacl.signing.SigningKey`` instance.
    """
    if not _NACL_AVAILABLE:
        raise ImportError("pynacl is required for checkpoint signing")

    body = {k: v for k, v in checkpoint.items() if k not in ("signature", "signer_key_hash")}
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    sig = signing_key.sign(canonical.encode("utf-8")).signature.hex()
    signed = dict(body)
    signed["signature"] = sig
    signed["signer_key_hash"] = hashlib.sha256(
        signing_key.verify_key.encode()
    ).hexdigest()
    return signed


def verify_checkpoint_signature(checkpoint: dict[str, Any], verify_key: Any) -> tuple[bool, str]:
    """Verify the embedded signature on *checkpoint* against *verify_key*.

    Returns ``(True, "ok")`` or ``(False, reason)``.
    """
    if not _NACL_AVAILABLE:
        return False, "pynacl not available"

    sig_hex = checkpoint.get("signature")
    if not sig_hex:
        return False, "no signature field"

    body = {k: v for k, v in checkpoint.items() if k not in ("signature", "signer_key_hash")}
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    try:
        from nacl.signing import VerifyKey
        vk = verify_key if isinstance(verify_key, VerifyKey) else VerifyKey(bytes.fromhex(verify_key))
        vk.verify(canonical.encode("utf-8"), bytes.fromhex(sig_hex))
        return True, "ok"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


# ---------------------------------------------------------------------------
# Publication helpers
# ---------------------------------------------------------------------------


def publish_checkpoint_file(
    checkpoint: dict[str, Any],
    out_dir: Path,
    *,
    stamp: str | None = None,
) -> Path:
    """Write *checkpoint* to a timestamped file under *out_dir*.

    Returns the resolved path of the written file.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if stamp is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    village_id = checkpoint.get("village_id", "unknown")
    out_path = out_dir / f"checkpoint.{village_id}.{stamp}.json"
    out_path.write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path.resolve()


def load_checkpoint_file(path: Path) -> dict[str, Any]:
    """Load a checkpoint artifact from *path*."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Peer fetch
# ---------------------------------------------------------------------------


def fetch_peer_checkpoint(base_url: str, village_id: str, *, token: str | None = None) -> dict[str, Any]:
    """Fetch the latest transparency checkpoint from a remote PolicyMesh node.

    Calls ``GET <base_url>/villages/<village_id>/transparency/checkpoint``.

    Parameters
    ----------
    base_url:
        Base URL of the remote node, e.g. ``"https://peer.example.org"``.
    village_id:
        Village identifier on the remote node.
    token:
        Optional bearer token for authenticated endpoints.

    Raises
    ------
    ImportError
        If ``requests`` is not installed.
    requests.HTTPError
        If the remote returns a non-2xx response.
    """
    if not _REQUESTS_AVAILABLE:
        raise ImportError("requests is required for fetch_peer_checkpoint")

    url = f"{base_url.rstrip('/')}/villages/{village_id}/transparency/checkpoint"
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = _requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


class CheckpointComparisonReport:
    """Structured comparison of a local and a peer transparency checkpoint."""

    def __init__(
        self,
        *,
        village_id: str,
        compared_at: str,
        local_checkpoint_hash: str,
        peer_checkpoint_hash: str,
        local_entry_count: int,
        peer_entry_count: int,
        local_latest_policy_hash: str,
        peer_latest_policy_hash: str,
        drift_class: str,
        status: str,
        notes: list[str],
    ) -> None:
        self.village_id = village_id
        self.compared_at = compared_at
        self.local_checkpoint_hash = local_checkpoint_hash
        self.peer_checkpoint_hash = peer_checkpoint_hash
        self.local_entry_count = local_entry_count
        self.peer_entry_count = peer_entry_count
        self.local_latest_policy_hash = local_latest_policy_hash
        self.peer_latest_policy_hash = peer_latest_policy_hash
        self.drift_class = drift_class
        self.status = status
        self.notes = notes

    def as_dict(self) -> dict[str, Any]:
        return {
            "village_id": self.village_id,
            "compared_at": self.compared_at,
            "local_checkpoint_hash": self.local_checkpoint_hash,
            "peer_checkpoint_hash": self.peer_checkpoint_hash,
            "local_entry_count": self.local_entry_count,
            "peer_entry_count": self.peer_entry_count,
            "local_latest_policy_hash": self.local_latest_policy_hash,
            "peer_latest_policy_hash": self.peer_latest_policy_hash,
            "drift_class": self.drift_class,
            "status": self.status,
            "notes": self.notes,
        }


def compare_checkpoints(
    local: dict[str, Any],
    peer: dict[str, Any],
) -> CheckpointComparisonReport:
    """Compare two checkpoint artifacts and classify any observed divergence.

    The comparison uses the ``drift_classes`` taxonomy:

    - ``"aligned"`` — both nodes agree on policy hash and entry count
    - ``"publication_lag"`` — policy hashes match but entry counts differ
      (peer is behind in publication)
    - ``"policy_divergence"`` — policy hashes differ, indicating a real
      governance disagreement
    - ``"unknown"`` — insufficient data to classify

    Returns a :class:`CheckpointComparisonReport`.
    """
    from links.drift_classes import classify_checkpoint_drift  # local import to avoid circularity

    local_hash = local.get("checkpoint_hash", "")
    peer_hash = peer.get("checkpoint_hash", "")
    local_policy = local.get("latest_policy_hash", "")
    peer_policy = peer.get("latest_policy_hash", "")
    local_count = local.get("entry_count", 0)
    peer_count = peer.get("entry_count", 0)
    village_id = local.get("village_id") or peer.get("village_id") or "unknown"

    drift_class, notes = classify_checkpoint_drift(
        local_policy_hash=local_policy,
        peer_policy_hash=peer_policy,
        local_entry_count=local_count,
        peer_entry_count=peer_count,
    )

    status = "aligned" if drift_class == "aligned" else "drift"

    return CheckpointComparisonReport(
        village_id=village_id,
        compared_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        local_checkpoint_hash=local_hash,
        peer_checkpoint_hash=peer_hash,
        local_entry_count=local_count,
        peer_entry_count=peer_count,
        local_latest_policy_hash=local_policy,
        peer_latest_policy_hash=peer_policy,
        drift_class=drift_class,
        status=status,
        notes=notes,
    )


def write_comparison_report(
    report: CheckpointComparisonReport,
    out_dir: Path,
    *,
    stamp: str | None = None,
) -> Path:
    """Write *report* as a JSON artifact under *out_dir*."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if stamp is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"checkpoint_compare.{report.village_id}.{stamp}.json"
    out_path.write_text(
        json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path.resolve()
