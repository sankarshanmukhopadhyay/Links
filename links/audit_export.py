from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable, Dict, Any, List, Optional, Tuple

from nacl.signing import SigningKey

from .file_lock import locked_open


def iter_audit_events(audit_log_path: Path) -> Iterable[Dict[str, Any]]:
    if not audit_log_path.exists():
        return []
    # JSONL
    def _gen():
        with locked_open(audit_log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    # Skip malformed lines; keep export resilient
                    continue
    return _gen()


def export_audit_json(audit_log_path: Path, out_path: Path) -> Tuple[str, int]:
    events = list(iter_audit_events(audit_log_path))
    payload = {"format": "links.audit.export.v1", "count": len(events), "events": events}
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    return digest, len(events)


def export_audit_csv(audit_log_path: Path, out_path: Path) -> Tuple[str, int]:
    events = list(iter_audit_events(audit_log_path))
    # Flatten basic fields; keep extras as JSON
    rows: List[Dict[str, Any]] = []
    for e in events:
        row = {
            "ts": e.get("ts") or e.get("time") or "",
            "event_type": e.get("event_type") or e.get("type") or "",
            "village_id": e.get("village_id") or "",
            "actor": e.get("actor") or "",
            "policy_hash": e.get("policy_hash") or "",
            "bundle_id": e.get("bundle_id") or "",
            "details": json.dumps({k: v for k, v in e.items() if k not in {"ts","time","event_type","type","village_id","actor","policy_hash","bundle_id"}}, ensure_ascii=False, sort_keys=True),
        }
        rows.append(row)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["ts","event_type","village_id","actor","policy_hash","bundle_id","details"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    data = out_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return digest, len(events)


def sign_digest_hex(digest_hex: str, signing_key: SigningKey) -> str:
    sig = signing_key.sign(bytes.fromhex(digest_hex)).signature
    return sig.hex()
