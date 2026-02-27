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


def write_denial_artifact(
    out_path: Path,
    *,
    village_id: str,
    subject_type: str,  # bundle|policy_update|other
    subject_id: str,
    reason: str,
    signing_key: SigningKey,
    actor: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    art: Dict[str, Any] = {
        "format": "links.denial.v1",
        "ts": utc_now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "village_id": village_id,
        "actor": actor,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "reason": reason,
        "meta": meta or {},
    }
    payload = canonical_json(art)
    art["artifact_hash"] = sha256_hex(payload)
    art["signature"] = signing_key.sign(payload).signature.hex()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with locked_open(out_path, "w") as f:
        f.write(json.dumps(art, ensure_ascii=False, sort_keys=True, indent=2))
    return art
