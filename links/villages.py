from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class VillagePolicy(BaseModel):
    visibility: str = Field(default="village", description="private|village|public")
    allowed_predicates: list[str] = Field(default_factory=lambda: ["links.weighted_to"])
    max_window_days: int = 30
    min_signature_alg: str = "Ed25519"
    allow_unverified: bool = False
    retention_days: int = 90
    rate_limit_per_min: int = 60


class VillageGovernance(BaseModel):
    admins: list[str] = Field(default_factory=list)
    decision_model: str = "admin-consensus"


class Village(BaseModel):
    village_id: str
    name: str
    description: str = ""
    created_at: datetime
    governance: VillageGovernance
    policy: VillagePolicy


class VillageMember(BaseModel):
    member_id: str
    role: str = "member"  # admin|member|observer
    added_at: datetime
    token_hash: str


def village_dir(root: Path, village_id: str) -> Path:
    return root / "villages" / village_id


def save_village(root: Path, v: Village) -> Path:
    vd = village_dir(root, v.village_id)
    vd.mkdir(parents=True, exist_ok=True)
    p = vd / "village.json"
    p.write_text(v.model_dump_json(indent=2), encoding="utf-8")
    (vd / "members.jsonl").touch(exist_ok=True)
    return p


def load_village(root: Path, village_id: str) -> Village:
    p = village_dir(root, village_id) / "village.json"
    return Village.model_validate_json(p.read_text(encoding="utf-8"))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def add_member(root: Path, village_id: str, member_id: str, role: str, token_plain: str) -> VillageMember:
    vd = village_dir(root, village_id)
    if not (vd / "village.json").exists():
        raise FileNotFoundError("Village not found")
    m = VillageMember(
        member_id=member_id,
        role=role,
        added_at=utc_now(),
        token_hash=hash_token(token_plain),
    )
    mp = vd / "members.jsonl"
    with mp.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "member_id": m.member_id,
            "role": m.role,
            "added_at": iso_utc(m.added_at),
            "token_hash": m.token_hash
        }, ensure_ascii=False) + "\n")
    return m


def list_members(root: Path, village_id: str) -> list[dict]:
    mp = village_dir(root, village_id) / "members.jsonl"
    if not mp.exists():
        return []
    out = []
    with mp.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def authorize(root: Path, village_id: str, token_plain: str) -> Optional[dict]:
    want = hash_token(token_plain)
    for m in list_members(root, village_id):
        if m.get("token_hash") == want:
            return m
    return None


def enforce_policy_on_bundle(village: Village, bundle: dict) -> tuple[bool, str]:
    window = int(bundle.get("window_days", 0))
    if window > village.policy.max_window_days:
        return False, f"bundle window_days={window} exceeds max_window_days={village.policy.max_window_days}"
    allowed = set(village.policy.allowed_predicates)
    for c in bundle.get("claims", []):
        pred = c.get("predicate")
        if pred and pred not in allowed:
            return False, f"predicate '{pred}' not allowed"
    return True, "ok"
