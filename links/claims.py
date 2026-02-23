from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

from .models import Link


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def short_hash(data: bytes, n: int = 32) -> str:
    return hashlib.sha256(data).hexdigest()[:n]


class Claim(BaseModel):
    issuer: str
    subject: str
    predicate: str
    object: Optional[str] = None
    value: Optional[Any] = None
    window_days: int
    computed_at: datetime
    derivation: Optional[str] = None
    evidence: list[str] = Field(default_factory=list)


class ClaimBundle(BaseModel):
    bundle_id: str
    issuer: str
    created_at: datetime
    window_days: int
    claims: list[Claim]
    signature_alg: str = "Ed25519"
    public_key: Optional[str] = None
    signature: Optional[str] = None


def bundle_payload_for_signing(bundle: ClaimBundle) -> dict:
    d = bundle.model_dump()
    d.pop("signature", None)
    d.pop("public_key", None)
    return d


def compute_bundle_id(payload: dict) -> str:
    return short_hash(canonical_json(payload), 32)


def build_bundle_from_edges(
    edges_json_path: Path,
    issuer: str,
    window_days: int,
    predicate: str = "links.weighted_to",
    derivation: str = "log(1 + count_30d)",
) -> ClaimBundle:
    edges = json.loads(Path(edges_json_path).read_text(encoding="utf-8"))
    created = utc_now()
    computed = created

    claims: list[Claim] = []
    for e in edges:
        link = Link.model_validate(e)
        claims.append(Claim(
            issuer=issuer,
            subject=link.from_entity_id,
            predicate=predicate,
            object=link.to_entity_id,
            value=link.weight,
            window_days=window_days,
            computed_at=computed,
            derivation=derivation,
            evidence=[],
        ))

    provisional = ClaimBundle(
        bundle_id="",
        issuer=issuer,
        created_at=created,
        window_days=window_days,
        claims=claims,
    )
    payload = bundle_payload_for_signing(provisional)
    bundle_id = compute_bundle_id(payload)
    return provisional.model_copy(update={"bundle_id": bundle_id})


def load_signing_key(path: Path) -> SigningKey:
    data = path.read_bytes()
    try:
        seed = base64.b64decode(data.strip())
    except Exception:
        seed = data
    if len(seed) < 32:
        raise ValueError("Signing key seed must be at least 32 bytes (Ed25519).")
    return SigningKey(seed[:32])


def sign_bundle(bundle: ClaimBundle, signing_key: SigningKey) -> ClaimBundle:
    payload = bundle_payload_for_signing(bundle)
    payload_bytes = canonical_json(payload)
    sig = signing_key.sign(payload_bytes).signature
    pub = signing_key.verify_key.encode()
    return bundle.model_copy(update={
        "public_key": base64.b64encode(pub).decode("utf-8"),
        "signature": base64.b64encode(sig).decode("utf-8"),
    })


def verify_bundle(bundle: ClaimBundle) -> bool:
    if not bundle.public_key or not bundle.signature:
        return False
    payload = bundle_payload_for_signing(bundle)
    expected_id = compute_bundle_id(payload)
    if bundle.bundle_id != expected_id:
        return False
    vk = VerifyKey(base64.b64decode(bundle.public_key))
    try:
        vk.verify(canonical_json(payload), base64.b64decode(bundle.signature))
        return True
    except BadSignatureError:
        return False


def write_bundle(path: Path, bundle: ClaimBundle) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")


def read_bundle(path: Path) -> ClaimBundle:
    return ClaimBundle.model_validate_json(path.read_text(encoding="utf-8"))
