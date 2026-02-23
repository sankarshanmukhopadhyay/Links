from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

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


class VillagePolicyUpdate(BaseModel):
    village_id: str
    created_at: datetime
    actor: Optional[str] = None
    policy: dict = Field(default_factory=dict)
    policy_hash: str

    signature_alg: str = "Ed25519"
    public_key: Optional[str] = None
    signature: Optional[str] = None


def payload_for_signing(u: VillagePolicyUpdate) -> dict:
    d = u.model_dump()
    d.pop("signature", None)
    d.pop("public_key", None)
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


def sign_update(u: VillagePolicyUpdate, signing_key: SigningKey) -> VillagePolicyUpdate:
    payload = payload_for_signing(u)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    return u.model_copy(update={
        "public_key": base64.b64encode(pub).decode("utf-8"),
        "signature": base64.b64encode(sig).decode("utf-8"),
    })


def verify_update(u: VillagePolicyUpdate) -> bool:
    # validate hash
    if u.policy_hash != compute_policy_hash(u.policy):
        return False
    if not u.public_key or not u.signature:
        return False
    payload = payload_for_signing(u)
    vk = VerifyKey(base64.b64decode(u.public_key))
    try:
        vk.verify(canonical_json(payload), base64.b64decode(u.signature))
        return True
    except BadSignatureError:
        return False
