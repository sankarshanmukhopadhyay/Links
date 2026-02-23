from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .store import ingest_bundle_file
from .audit import write_audit, AuditEvent


def quarantine_dir(store_root: Path, village_id: Optional[str]) -> Path:
    q = store_root / "quarantine"
    if village_id:
        q = q / village_id
    q.mkdir(parents=True, exist_ok=True)
    return q


def rejected_dir(store_root: Path, village_id: Optional[str]) -> Path:
    r = store_root / "rejected"
    if village_id:
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


def approve_quarantine(store_root: Path, bundle_path: Path) -> tuple[bool, str]:
    ok, msg = ingest_bundle_file(bundle_path, store_root=store_root)
    if ok:
        bundle_path.unlink(missing_ok=True)
        write_audit(store_root, AuditEvent(action="quarantine.approve", bundle_id=bundle_path.stem, reason=msg))
    return ok, msg


def reject_quarantine(store_root: Path, bundle_path: Path, village_id: Optional[str], reason: str) -> tuple[bool, str]:
    rd = rejected_dir(store_root, village_id)
    out = rd / bundle_path.name
    out.write_text(bundle_path.read_text(encoding="utf-8"), encoding="utf-8")
    bundle_path.unlink(missing_ok=True)
    write_audit(store_root, AuditEvent(action="quarantine.reject", bundle_id=bundle_path.stem, village_id=village_id, reason=reason))
    return True, f"moved to rejected: {out}"
