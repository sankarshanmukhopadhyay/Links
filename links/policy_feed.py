from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Iterable, Tuple

from .policy_updates import VillagePolicyUpdate, verify_update, key_hash_from_public_key_b64


def _updates_dir(villages_root: Path, village_id: str) -> Path:
    d = villages_root / "villages" / village_id / "policy_updates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def store_policy_update(villages_root: Path, u: VillagePolicyUpdate) -> Path:
    d = _updates_dir(villages_root, u.village_id)
    # Filename sortable by created_at
    ts = u.created_at.astimezone(__import__("datetime").timezone.utc).isoformat().replace("+00:00","Z").replace(":","").replace("-","")
    p = d / f"{ts}.{u.policy_hash}.json"
    p.write_text(u.model_dump_json(indent=2), encoding="utf-8")
    return p


def iter_policy_updates(villages_root: Path, village_id: str) -> Iterable[VillagePolicyUpdate]:
    d = _updates_dir(villages_root, village_id)
    for p in sorted(d.glob("*.json")):
        try:
            yield VillagePolicyUpdate.model_validate_json(p.read_text(encoding="utf-8"))
        except Exception:
            continue


def latest_policy_update(villages_root: Path, village_id: str) -> Optional[VillagePolicyUpdate]:
    ups = list(iter_policy_updates(villages_root, village_id))
    if not ups:
        return None
    # Reconcile rule: pick max by (created_at, policy_hash)
    ups.sort(key=lambda u: (u.created_at, u.policy_hash), reverse=True)
    return ups[0]


def filter_updates_since(villages_root: Path, village_id: str, since_hash: Optional[str]) -> list[VillagePolicyUpdate]:
    ups = list(iter_policy_updates(villages_root, village_id))
    ups.sort(key=lambda u: (u.created_at, u.policy_hash))
    if not since_hash:
        return ups
    out = []
    seen = False
    for u in ups:
        if seen:
            out.append(u)
        if u.policy_hash == since_hash:
            seen = True
    return out


def signer_allowed(policy: dict, u: VillagePolicyUpdate) -> Tuple[bool, str]:
    require_sig = bool(policy.get("require_policy_signature", False))
    allow = set(policy.get("policy_signer_allowlist", []) or [])
    if require_sig:
        if not (u.public_key and u.signature):
            return False, "signature required"
        if not verify_update(u):
            return False, "signature invalid"
        signer_hash = key_hash_from_public_key_b64(u.public_key)
        if allow and signer_hash not in allow:
            return False, "signer not allowlisted"
        return True, "ok"
    # signatures optional: if provided, must verify
    if u.public_key or u.signature:
        if not verify_update(u):
            return False, "signature invalid"
        signer_hash = key_hash_from_public_key_b64(u.public_key) if u.public_key else None
        if allow and signer_hash and signer_hash not in allow:
            return False, "signer not allowlisted"
    return True, "ok"
