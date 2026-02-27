from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .claims import ClaimBundle, verify_bundle
from .store import ingest_bundle_file
from .audit import write_audit, AuditEvent, policy_hash
from .villages import load_village, enforce_policy_on_bundle, issuer_key_hash_from_public_key_b64, issuer_allowed
from .file_lock import locked_open
from .validate import validate_village_id
from .denials import write_denial_artifact
from .keys import load_signing_key_from_env


def quarantine_dir(store_root: Path, village_id: Optional[str]) -> Path:
    q = store_root / "quarantine"
    if village_id:
        validate_village_id(village_id)
        q = q / village_id
    q.mkdir(parents=True, exist_ok=True)
    return q


def rejected_dir(store_root: Path, village_id: Optional[str]) -> Path:
    r = store_root / "rejected"
    if village_id:
        validate_village_id(village_id)
        r = r / village_id
    r.mkdir(parents=True, exist_ok=True)
    return r


def quarantine_bundle(store_root: Path, bundle_obj: dict, bundle_id: str, village_id: Optional[str], reason: str, issuer_key_hash: Optional[str] = None) -> Path:
    qd = quarantine_dir(store_root, village_id)
    p = qd / f"{bundle_id}.json"
    p.write_text(json.dumps(bundle_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    write_audit(store_root, AuditEvent(action="ingest.quarantine", bundle_id=bundle_id, village_id=village_id, issuer_key_hash=issuer_key_hash, reason=reason))
    return p


def list_quarantine(store_root: Path, village_id: Optional[str] = None) -> list[Path]:
    qd = quarantine_dir(store_root, village_id)
    return sorted(qd.glob("*.json"))


def approve_quarantine(store_root: Path, bundle_path: Path, villages_root: Path = Path("data")) -> tuple[bool, str]:
    """
    Approve a quarantined bundle, but re-check current policy before ingestion.
    - verifies signature + bundle_id
    - if village_id present, loads current village policy and re-checks predicates/window/issuer allowlists
    """
    obj = json.loads(bundle_path.read_text(encoding="utf-8"))
    cb = ClaimBundle.model_validate(obj)
    if not verify_bundle(cb):
        return False, "bundle failed verification (cannot approve)"
    village_id = getattr(cb, "village_id", None)

    if village_id:
        v = load_village(villages_root, village_id)
        okp, msgp = enforce_policy_on_bundle(v, obj)
        if not okp:
            reason = f"policy no longer allows approval: {msgp}"
            try:
                sk = load_signing_key_from_env()
                out = rejected_dir(store_root, village_id) / f"{bundle_path.stem}.denial.json"
                write_denial_artifact(out, village_id=village_id, subject_type="bundle", subject_id=bundle_path.stem, reason=reason, signing_key=sk)
            except Exception:
                pass
            return False, reason
        issuer_hash = issuer_key_hash_from_public_key_b64(cb.public_key) if cb.public_key else None
        if issuer_hash and not issuer_allowed(v.policy, issuer_hash):
            return False, "policy no longer allows issuer"


    # Village-level submission quota (if configured)
    if village_id:
        v = load_village(villages_root, village_id)
        quota = getattr(v.policy, "submission_quota_per_day", 0) or 0
        if quota > 0:
            used = _count_quarantine_approvals_today(store_root, village_id)
            if used >= quota:
                reason = f"submission quota exceeded for UTC day (used {used}/{quota})"
                # Emit a signed denial artifact if node key is available
                try:
                    sk = load_signing_key_from_env()
                    out = rejected_dir(store_root, village_id) / f"{bundle_path.stem}.denial.json"
                    write_denial_artifact(out, village_id=village_id, subject_type="bundle", subject_id=bundle_path.stem, reason=reason, signing_key=sk)
                except Exception:
                    pass
                return False, reason
    
    ok, msg = ingest_bundle_file(bundle_path, store_root=store_root)
    if ok:
        bundle_path.unlink(missing_ok=True)
        write_audit(store_root, AuditEvent(action="quarantine.approve", bundle_id=bundle_path.stem, village_id=village_id, reason=msg))
    return ok, msg


def reject_quarantine(store_root: Path, bundle_path: Path, village_id: Optional[str], reason: str) -> tuple[bool, str]:
    rd = rejected_dir(store_root, village_id)
    out = rd / bundle_path.name
    out.write_text(bundle_path.read_text(encoding="utf-8"), encoding="utf-8")
    bundle_path.unlink(missing_ok=True)
    write_audit(store_root, AuditEvent(action="quarantine.reject", bundle_id=bundle_path.stem, village_id=village_id, reason=reason))
    return True, f"moved to rejected: {out}"


def _count_quarantine_approvals_today(store_root: Path, village_id: str) -> int:
    """Count today's quarantine.approve events for a village (UTC day)."""
    audit_path = store_root / "audit" / "audit.log.jsonl"
    if not audit_path.exists():
        return 0
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date()
    n = 0
    with locked_open(audit_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if ev.get("action") != "quarantine.approve":
                continue
            if ev.get("village_id") != village_id:
                continue
            ts = ev.get("ts") or ""
            try:
                # ISO-8601 Z
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                continue
            if dt.date() == today:
                n += 1
    return n
