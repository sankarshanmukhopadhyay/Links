from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional, List, Set

from pydantic import BaseModel, Field
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_hash_from_public_key_b64(public_key_b64: str) -> str:
    pk = base64.b64decode(public_key_b64)
    return hashlib.sha256(pk).hexdigest()


class SignatureEntry(BaseModel):
    public_key: str  # base64
    signature: str   # base64


class VillagePolicyUpdate(BaseModel):
    """
    A policy update artifact supporting either:
      - legacy single signature fields: public_key + signature
      - multisig quorum via signatures[]
    Signatures cover the canonical JSON payload of the update with all signature material removed.
    """
    village_id: str
    created_at: datetime
    actor: Optional[str] = None
    policy: dict = Field(default_factory=dict)
    policy_hash: str

    signature_alg: str = "Ed25519"

    # Legacy single signature (backwards compatible)
    public_key: Optional[str] = None
    signature: Optional[str] = None

    # New multisig support
    signatures: List[SignatureEntry] = Field(default_factory=list)


def payload_for_signing(u: VillagePolicyUpdate) -> dict:
    d = u.model_dump()
    # remove signature material (legacy + multisig)
    d.pop("signature", None)
    d.pop("public_key", None)
    d.pop("signatures", None)
    return d


def compute_policy_hash(policy: dict) -> str:
    return sha256_hex(canonical_json(policy))


def build_update(village_id: str, policy: dict, actor: Optional[str] = None) -> VillagePolicyUpdate:
    ph = compute_policy_hash(policy)
    return VillagePolicyUpdate(
        village_id=village_id,
        created_at=utc_now(),
        actor=actor,
        policy=policy,
        policy_hash=ph,
    )


def sign_update_legacy(u: VillagePolicyUpdate, signing_key: SigningKey) -> VillagePolicyUpdate:
    """
    Produce a legacy single-signature update (public_key/signature).
    """
    payload = payload_for_signing(u)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    return u.model_copy(update={
        "public_key": base64.b64encode(pub).decode("utf-8"),
        "signature": base64.b64encode(sig).decode("utf-8"),
    })


def add_signature(u: VillagePolicyUpdate, signing_key: SigningKey) -> VillagePolicyUpdate:
    """
    Append a signature entry to u.signatures (multisig).
    Ensures uniqueness by public_key hash.
    """
    payload = payload_for_signing(u)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    entry = SignatureEntry(
        public_key=base64.b64encode(pub).decode("utf-8"),
        signature=base64.b64encode(sig).decode("utf-8"),
    )
    # de-dup by signer key hash
    seen: Set[str] = set()
    out = []
    for e in (u.signatures or []):
        h = key_hash_from_public_key_b64(e.public_key)
        if h in seen:
            continue
        seen.add(h)
        out.append(e)
    h_new = key_hash_from_public_key_b64(entry.public_key)
    if h_new not in seen:
        out.append(entry)
    return u.model_copy(update={"signatures": out})


def _verify_one(payload: dict, public_key_b64: str, signature_b64: str) -> bool:
    vk = VerifyKey(base64.b64decode(public_key_b64))
    try:
        vk.verify(canonical_json(payload), base64.b64decode(signature_b64))
        return True
    except BadSignatureError:
        return False


def verify_update_any(u: VillagePolicyUpdate) -> bool:
    """
    Verify that policy_hash matches and at least one signature (legacy or in signatures[]) verifies.
    """
    if u.policy_hash != compute_policy_hash(u.policy):
        return False
    payload = payload_for_signing(u)

    # multisig list first
    for e in (u.signatures or []):
        if _verify_one(payload, e.public_key, e.signature):
            return True

    # legacy
    if u.public_key and u.signature:
        return _verify_one(payload, u.public_key, u.signature)

    return False


def verify_update_quorum(u: VillagePolicyUpdate, required_m: int, signer_allowlist: list[str] | None = None) -> tuple[bool, str]:
    """
    Verify policy_hash and that >= required_m distinct allowlisted signers have produced valid signatures.
    - required_m must be >= 1
    - signer_allowlist contains sha256(public_key_bytes) values; if empty/None, any signer is acceptable.
    """
    if required_m < 1:
        return False, "invalid quorum threshold"
    if u.policy_hash != compute_policy_hash(u.policy):
        return False, "policy_hash mismatch"

    payload = payload_for_signing(u)
    allow = set(signer_allowlist or [])
    valid_signers: Set[str] = set()

    # multisig entries
    for e in (u.signatures or []):
        kh = key_hash_from_public_key_b64(e.public_key)
        if allow and kh not in allow:
            continue
        if _verify_one(payload, e.public_key, e.signature):
            valid_signers.add(kh)

    # legacy signature counts as one signer
    if u.public_key and u.signature:
        kh = key_hash_from_public_key_b64(u.public_key)
        if (not allow) or (kh in allow):
            if _verify_one(payload, u.public_key, u.signature):
                valid_signers.add(kh)

    if len(valid_signers) >= required_m:
        return True, "ok"
    return False, f"quorum not met (valid={len(valid_signers)} required={required_m})"
