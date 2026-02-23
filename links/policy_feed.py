from __future__ import annotations

from pathlib import Path
from typing import Optional, Iterable, Tuple, Set
from datetime import timezone

from .policy_updates import VillagePolicyUpdate, verify_update_any, verify_update_quorum


def _updates_dir(villages_root: Path, village_id: str) -> Path:
    d = villages_root / "villages" / village_id / "policy_updates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def store_policy_update(villages_root: Path, u: VillagePolicyUpdate) -> Path:
    d = _updates_dir(villages_root, u.village_id)
    ts = u.created_at.astimezone(timezone.utc).isoformat().replace("+00:00","Z").replace(":","").replace("-","")
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
    """
    Enforce policy signature rules with optional quorum:
    - If require_policy_signature=true:
        - enforce valid signatures
        - enforce allowlist if provided
        - enforce M-of-N threshold via policy_signature_threshold_m (default 1)
    - If signatures are optional:
        - if any signature material is present, it must verify (at least one valid)
        - if allowlist is present, signatures must come from allowlisted keys
    """
    require_sig = bool(policy.get("require_policy_signature", False))
    allowlist = list(policy.get("policy_signer_allowlist", []) or [])
    threshold_m = int(policy.get("policy_signature_threshold_m", 1) or 1)

    if require_sig:
        ok, msg = verify_update_quorum(u, required_m=threshold_m, signer_allowlist=allowlist if allowlist else None)
        return ok, msg

    # signatures optional: if any signature material exists, require at least one valid signature
    has_any = bool(u.signatures) or bool(u.public_key) or bool(u.signature)
    if has_any:
        # if allowlist present, require at least one valid allowlisted signature
        if allowlist:
            ok, msg = verify_update_quorum(u, required_m=1, signer_allowlist=allowlist)
            return ok, msg
        if not verify_update_any(u):
            return False, "signature invalid"
    return True, "ok"
