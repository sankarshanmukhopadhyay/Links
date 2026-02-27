from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from nacl.signing import SigningKey

from .file_lock import locked_open
from .policy_updates import canonical_json, sha256_hex


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def transparency_log_path(store_root: Path, village_id: str) -> Path:
    p = store_root / "transparency" / village_id / "policy_log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def append_transparency_entry(
    store_root: Path,
    village_id: str,
    policy_hash: str,
    update_hash: Optional[str],
    signing_key: SigningKey,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "ts": utc_now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "village_id": village_id,
        "policy_hash": policy_hash,
        "update_hash": update_hash,
        "meta": meta or {},
    }
    payload = canonical_json(entry)
    entry["entry_hash"] = sha256_hex(payload)
    entry["signature"] = signing_key.sign(payload).signature.hex()
    with locked_open(transparency_log_path(store_root, village_id), "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry
