from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

from pydantic import BaseModel, Field
from nacl.signing import SigningKey

from .policy_updates import (
    SignatureEntry,
    canonical_json,
    sha256_hex,
    key_hash_from_public_key_b64,
    payload_for_signing,  # type: ignore
)
from .policy_updates import VillagePolicyUpdate, add_signature, verify_update_any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TrustAnchorEntry(BaseModel):
    village_id: str
    created_at: datetime
    actor: Optional[str] = None

    action: str = Field(description="register|rotate|revoke")
    anchor_id: str
    anchor_public_key: Optional[str] = None  # base64 public key bytes
    anchor_key_hash: Optional[str] = None    # sha256(public_key_bytes)

    previous_anchor_key_hash: Optional[str] = None
    reason: Optional[str] = None

    signature_alg: str = "Ed25519"
    signatures: List[SignatureEntry] = Field(default_factory=list)


def _anchors_dir(villages_root: Path, village_id: str) -> Path:
    d = villages_root / "villages" / village_id / "trust_anchors"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _payload_for_signing(e: TrustAnchorEntry) -> dict:
    d = e.model_dump()
    d.pop("signatures", None)
    return d


def add_anchor_signature(e: TrustAnchorEntry, signing_key: SigningKey) -> TrustAnchorEntry:
    payload = _payload_for_signing(e)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    entry = SignatureEntry(
        public_key=base64.b64encode(pub).decode("utf-8"),
        signature=base64.b64encode(sig).decode("utf-8"),
    )

    seen: Set[str] = set()
    out: List[SignatureEntry] = []
    for s in (e.signatures or []):
        kh = key_hash_from_public_key_b64(s.public_key)
        if kh in seen:
            continue
        seen.add(kh)
        out.append(s)

    kh_new = key_hash_from_public_key_b64(entry.public_key)
    if kh_new not in seen:
        out.append(entry)
    return e.model_copy(update={"signatures": out})


def verify_anchor_entry_any(e: TrustAnchorEntry) -> bool:
    if not e.signatures:
        return False
    payload = _payload_for_signing(e)
    for s in e.signatures:
        try:
            from nacl.signing import VerifyKey
            from nacl.exceptions import BadSignatureError
            vk = VerifyKey(base64.b64decode(s.public_key))
            vk.verify(canonical_json(payload), base64.b64decode(s.signature))
            return True
        except Exception:
            continue
    return False


def store_anchor_entry(villages_root: Path, e: TrustAnchorEntry) -> Path:
    d = _anchors_dir(villages_root, e.village_id)
    ts = e.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z").replace(":", "").replace("-", "")
    keyh = e.anchor_key_hash or "na"
    p = d / f"{ts}.{e.action}.{keyh}.json"
    p.write_text(e.model_dump_json(indent=2), encoding="utf-8")
    return p


def iter_anchor_entries(villages_root: Path, village_id: str) -> List[TrustAnchorEntry]:
    d = _anchors_dir(villages_root, village_id)
    out: List[TrustAnchorEntry] = []
    for p in sorted(d.glob("*.json")):
        try:
            out.append(TrustAnchorEntry.model_validate_json(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    out.sort(key=lambda x: (x.created_at, x.anchor_key_hash or ""))
    return out


def latest_active_anchor(villages_root: Path, village_id: str) -> Optional[TrustAnchorEntry]:
    entries = iter_anchor_entries(villages_root, village_id)
    active: Dict[str, TrustAnchorEntry] = {}
    for e in entries:
        if e.action in ("register", "rotate"):
            if e.anchor_key_hash:
                active[e.anchor_key_hash] = e
        if e.action == "revoke":
            if e.anchor_key_hash and e.anchor_key_hash in active:
                del active[e.anchor_key_hash]
    if not active:
        return None
    # pick latest by created_at
    return sorted(active.values(), key=lambda x: x.created_at, reverse=True)[0]
