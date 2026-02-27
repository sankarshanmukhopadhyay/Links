from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional, List, Set, Dict, Tuple

from pydantic import BaseModel, Field
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


# -----------------------------
# Helpers
# -----------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_default(o: Any):
    from datetime import datetime
    if isinstance(o, datetime):
        # Always serialize datetimes to ISO-8601 UTC strings
        if o.tzinfo is None:
            return o.replace(tzinfo=timezone.utc).isoformat().replace('+00:00','Z')
        return o.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_hash_from_public_key_b64(public_key_b64: str) -> str:
    """Key hash = sha256(public_key_bytes)."""
    pk = base64.b64decode(public_key_b64)
    return hashlib.sha256(pk).hexdigest()


def compute_policy_hash(policy: dict) -> str:
    return sha256_hex(canonical_json(policy))


# -----------------------------
# Models
# -----------------------------

class SignatureEntry(BaseModel):
    public_key: str  # base64 (Ed25519 public key bytes)
    signature: str   # base64


class QuorumRequirement(BaseModel):
    role: str
    min_signers: int = 1


class QuorumMetadata(BaseModel):
    """Explicit quorum metadata included inside the signed update artifact for audit clarity."""
    model: str = Field(default="m_of_n", description="m_of_n|weighted|role_based")
    threshold_m: Optional[int] = Field(default=None, description="M for m_of_n")
    threshold_weight: Optional[float] = Field(default=None, description="Total weight required for weighted quorum")

    # Optional snapshot of signer configuration used for evaluation
    signer_set_hash: Optional[str] = Field(default=None, description="sha256(canonical_json(policy_signers_snapshot))")
    role_requirements: List[QuorumRequirement] = Field(default_factory=list)


class PolicyChangeSummary(BaseModel):
    """Machine-readable summary of a policy change."""
    added: List[str] = Field(default_factory=list, description="JSON pointer paths added")
    removed: List[str] = Field(default_factory=list, description="JSON pointer paths removed")
    changed: List[str] = Field(default_factory=list, description="JSON pointer paths changed")


class VillagePolicyUpdate(BaseModel):
    """A signed policy update artifact.

    Backwards compatibility:
      - legacy single signature fields: public_key + signature
      - multisig quorum via signatures[]

    New governance features:
      - lifecycle states (proposal -> approved -> active)
      - policy versioning & rollback metadata
      - explicit quorum metadata for audit clarity
      - machine-readable change summaries (optional)
    """

    village_id: str
    created_at: datetime
    actor: Optional[str] = None

    # The effective policy content (for the requested lifecycle state).
    policy: dict = Field(default_factory=dict)

    # Hash of the policy content (canonical JSON).
    policy_hash: str

    # First-class policy version identifier (can be semantic or arbitrary); defaults to policy_hash when unset.
    policy_version_id: Optional[str] = None

    # Lifecycle: proposal -> approved -> active
    lifecycle_state: str = Field(default="proposal", description="proposal|approved|active|rolled_back")

    # Versioning / rollback linking
    previous_policy_hash: Optional[str] = None
    rollback_to_policy_hash: Optional[str] = None

    # Activation semantics (time and/or height)
    activation_time: Optional[datetime] = None
    activation_height: Optional[int] = None

    # Audit-friendly quorum metadata (signed)
    quorum: Optional[QuorumMetadata] = None

    # Optional machine-readable diff summary (signed)
    change_summary: Optional[PolicyChangeSummary] = None

    signature_alg: str = "Ed25519"

    # Legacy single signature (backwards compatible)
    public_key: Optional[str] = None
    signature: Optional[str] = None

    # Multisig support
    signatures: List[SignatureEntry] = Field(default_factory=list)


# -----------------------------
# Signing / verification
# -----------------------------

def payload_for_signing(u: VillagePolicyUpdate) -> dict:
    d = u.model_dump()
    # remove signature material (legacy + multisig)
    d.pop("signature", None)
    d.pop("public_key", None)
    d.pop("signatures", None)
    return d


def compute_update_hash(u: VillagePolicyUpdate) -> str:
    """Deterministic update hash for linking/manifests."""
    return sha256_hex(canonical_json(payload_for_signing(u)))


def build_update(
    village_id: str,
    policy: dict,
    actor: Optional[str] = None,
    *,
    lifecycle_state: str = "proposal",
    previous_policy_hash: Optional[str] = None,
    activation_time: Optional[datetime] = None,
    activation_height: Optional[int] = None,
    policy_version_id: Optional[str] = None,
    quorum: Optional[QuorumMetadata] = None,
    change_summary: Optional[PolicyChangeSummary] = None,
) -> VillagePolicyUpdate:
    ph = compute_policy_hash(policy)
    return VillagePolicyUpdate(
        village_id=village_id,
        created_at=utc_now(),
        actor=actor,
        policy=policy,
        policy_hash=ph,
        policy_version_id=policy_version_id or ph,
        lifecycle_state=lifecycle_state,
        previous_policy_hash=previous_policy_hash,
        activation_time=activation_time,
        activation_height=activation_height,
        quorum=quorum,
        change_summary=change_summary,
    )


def sign_update_legacy(u: VillagePolicyUpdate, signing_key: SigningKey) -> VillagePolicyUpdate:
    """Produce a legacy single-signature update (public_key/signature)."""
    payload = payload_for_signing(u)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    return u.model_copy(update={
        "public_key": base64.b64encode(pub).decode("utf-8"),
        "signature": base64.b64encode(sig).decode("utf-8"),
    })


def add_signature(u: VillagePolicyUpdate, signing_key: SigningKey) -> VillagePolicyUpdate:
    """Append a signature entry to u.signatures (multisig). Ensures uniqueness by public_key hash."""
    payload = payload_for_signing(u)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    entry = SignatureEntry(
        public_key=base64.b64encode(pub).decode("utf-8"),
        signature=base64.b64encode(sig).decode("utf-8"),
    )

    seen: Set[str] = set()
    out: List[SignatureEntry] = []
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
    """Verify policy_hash matches and at least one signature verifies."""
    if u.policy_hash != compute_policy_hash(u.policy):
        return False
    payload = payload_for_signing(u)

    for e in (u.signatures or []):
        if _verify_one(payload, e.public_key, e.signature):
            return True

    if u.public_key and u.signature:
        return _verify_one(payload, u.public_key, u.signature)

    return False


def verify_update_quorum(
    u: VillagePolicyUpdate,
    required_m: int,
    signer_allowlist: list[str] | None = None
) -> tuple[bool, str]:
    """Verify policy_hash and that >= required_m distinct allowlisted signers have valid signatures."""
    if required_m < 1:
        return False, "invalid quorum threshold"
    if u.policy_hash != compute_policy_hash(u.policy):
        return False, "policy_hash mismatch"

    payload = payload_for_signing(u)
    allow = set(signer_allowlist or [])
    valid_signers: Set[str] = set()

    for e in (u.signatures or []):
        kh = key_hash_from_public_key_b64(e.public_key)
        if allow and kh not in allow:
            continue
        if _verify_one(payload, e.public_key, e.signature):
            valid_signers.add(kh)

    if u.public_key and u.signature:
        kh = key_hash_from_public_key_b64(u.public_key)
        if (not allow) or (kh in allow):
            if _verify_one(payload, u.public_key, u.signature):
                valid_signers.add(kh)

    if len(valid_signers) >= required_m:
        return True, "ok"
    return False, f"quorum not met (valid={len(valid_signers)} required={required_m})"


def verify_update_weighted_quorum(
    u: VillagePolicyUpdate,
    weights_by_key_hash: Dict[str, float],
    required_weight: float,
    signer_allowlist: list[str] | None = None,
) -> Tuple[bool, str, float]:
    """Weighted quorum verification.

    - weights_by_key_hash: key_hash -> weight (float)
    - required_weight: threshold
    - signer_allowlist: optional allowlist (key hashes)
    Returns (ok, msg, achieved_weight)
    """
    if required_weight <= 0:
        return False, "invalid weight threshold", 0.0
    if u.policy_hash != compute_policy_hash(u.policy):
        return False, "policy_hash mismatch", 0.0

    payload = payload_for_signing(u)
    allow = set(signer_allowlist or [])
    achieved = 0.0
    counted: Set[str] = set()

    def maybe_count(pub_b64: str, sig_b64: str):
        nonlocal achieved
        kh = key_hash_from_public_key_b64(pub_b64)
        if kh in counted:
            return
        if allow and kh not in allow:
            return
        if not _verify_one(payload, pub_b64, sig_b64):
            return
        w = float(weights_by_key_hash.get(kh, 0.0))
        achieved += w
        counted.add(kh)

    for e in (u.signatures or []):
        maybe_count(e.public_key, e.signature)

    if u.public_key and u.signature:
        maybe_count(u.public_key, u.signature)

    if achieved >= required_weight:
        return True, "ok", achieved
    return False, f"weighted quorum not met (weight={achieved} required={required_weight})", achieved


def verify_update_role_based_quorum(
    u: VillagePolicyUpdate,
    roles_by_key_hash: Dict[str, List[str]],
    requirements: List[QuorumRequirement],
    signer_allowlist: list[str] | None = None,
) -> Tuple[bool, str, Dict[str, int]]:
    """Role-based quorum verification.

    Example: requirements=[{role:'core',min_signers:1},{role:'external',min_signers:1}]
    Returns (ok, msg, role_counts)
    """
    if u.policy_hash != compute_policy_hash(u.policy):
        return False, "policy_hash mismatch", {}
    payload = payload_for_signing(u)
    allow = set(signer_allowlist or [])

    role_counts: Dict[str, int] = {r.role: 0 for r in requirements}
    counted: Set[str] = set()

    def maybe_count(pub_b64: str, sig_b64: str):
        kh = key_hash_from_public_key_b64(pub_b64)
        if kh in counted:
            return
        if allow and kh not in allow:
            return
        if not _verify_one(payload, pub_b64, sig_b64):
            return
        counted.add(kh)
        for role in roles_by_key_hash.get(kh, []):
            if role in role_counts:
                role_counts[role] += 1

    for e in (u.signatures or []):
        maybe_count(e.public_key, e.signature)

    if u.public_key and u.signature:
        maybe_count(u.public_key, u.signature)

    missing = []
    for req in requirements:
        if role_counts.get(req.role, 0) < int(req.min_signers):
            missing.append(f"{req.role}({role_counts.get(req.role, 0)}/{req.min_signers})")

    if not missing:
        return True, "ok", role_counts
    return False, "role quorum not met: " + ", ".join(missing), role_counts
