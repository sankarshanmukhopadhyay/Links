from __future__ import annotations

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header

from .claims import ClaimBundle, verify_bundle
from .store import ingest_bundle_file
from .villages import load_village, authorize, enforce_policy_on_bundle, issuer_key_hash_from_public_key_b64, issuer_allowed, role_can
from .quarantine import quarantine_bundle
from .audit import write_audit, AuditEvent, policy_hash


def _latest_path(glob_it):
    candidates = sorted(list(glob_it), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def create_app(store_root: Path = Path("data/store"), inbox_root: Path = Path("data/inbox"), villages_root: Path = Path("data")) -> FastAPI:
    app = FastAPI(title="Links Claim Exchange", version="0.5.0")
    inbox_root.mkdir(parents=True, exist_ok=True)

    @app.get("/.well-known/links/claims/latest")
    def latest_bundle():
        p = _latest_path((store_root / "bundles").rglob("*.json")) if (store_root / "bundles").exists() else None
        if not p:
            raise HTTPException(status_code=404, detail="no bundles available")
        return json.loads(p.read_text(encoding="utf-8"))

    @app.get("/villages/{village_id}/claims/latest")
    def latest_village_bundle(village_id: str, authorization: str | None = Header(default=None)):
        token = _bearer_token(authorization)
        member = authorize(villages_root, village_id, token) if token else None
        if not member:
            raise HTTPException(status_code=403, detail="forbidden")

        v = load_village(villages_root, village_id)
        if not role_can(v.policy, member.get("role", "observer"), "pull"):
            raise HTTPException(status_code=403, detail="forbidden")

        bundles_dir = store_root / "bundles" / village_id
        if not bundles_dir.exists():
            raise HTTPException(status_code=404, detail="no bundles for village")
        p = _latest_path(bundles_dir.glob("*.json"))
        if not p:
            raise HTTPException(status_code=404, detail="no bundles for village")
        return json.loads(p.read_text(encoding="utf-8"))

    @app.post("/inbox")
    def post_inbox(bundle: dict):
        cb = ClaimBundle.model_validate(bundle)
        if not verify_bundle(cb):
            raise HTTPException(status_code=400, detail="invalid bundle (signature/bundle_id)")
        inbox_path = inbox_root / f"{cb.bundle_id}.json"
        inbox_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        ok, msg = ingest_bundle_file(inbox_path, store_root=store_root)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "ok", "message": msg, "bundle_id": cb.bundle_id}

    @app.post("/villages/{village_id}/inbox")
    def post_village_inbox(village_id: str, bundle: dict, authorization: str | None = Header(default=None)):
        token = _bearer_token(authorization)
        member = authorize(villages_root, village_id, token) if token else None
        if not member:
            raise HTTPException(status_code=403, detail="forbidden")

        v = load_village(villages_root, village_id)
        if not role_can(v.policy, member.get("role", "observer"), "push"):
            raise HTTPException(status_code=403, detail="forbidden")

        cb = ClaimBundle.model_validate(bundle)
        if not verify_bundle(cb):
            quarantine_bundle(store_root, bundle, cb.bundle_id, village_id, "invalid signature or bundle_id")
            raise HTTPException(status_code=400, detail="invalid bundle (signature/bundle_id)")

        issuer_hash = None
        if cb.public_key:
            issuer_hash = issuer_key_hash_from_public_key_b64(cb.public_key)
            if not issuer_allowed(v.policy, issuer_hash):
                quarantine_bundle(store_root, bundle, cb.bundle_id, village_id, "issuer not allowed", issuer_key_hash=issuer_hash)
                write_audit(store_root, AuditEvent(action="ingest.reject", bundle_id=cb.bundle_id, village_id=village_id, issuer_key_hash=issuer_hash, actor=member.get("member_id"), reason="issuer not allowed", policy_hash=policy_hash(v.policy.model_dump())))
                raise HTTPException(status_code=400, detail="policy violation: issuer not allowed")

        okp, msgp = enforce_policy_on_bundle(v, bundle)
        if not okp:
            quarantine_bundle(store_root, bundle, cb.bundle_id, village_id, f"policy violation: {msgp}", issuer_key_hash=issuer_hash)
            write_audit(store_root, AuditEvent(action="ingest.reject", bundle_id=cb.bundle_id, village_id=village_id, issuer_key_hash=issuer_hash, actor=member.get("member_id"), reason=msgp, policy_hash=policy_hash(v.policy.model_dump())))
            raise HTTPException(status_code=400, detail=f"policy violation: {msgp}")

        bundle["village_id"] = village_id
        bundle["visibility"] = "village"

        inbox_path = inbox_root / f"{village_id}.{cb.bundle_id}.json"
        inbox_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        ok, msg = ingest_bundle_file(inbox_path, store_root=store_root)
        if not ok:
            quarantine_bundle(store_root, bundle, cb.bundle_id, village_id, f"ingest failed: {msg}", issuer_key_hash=issuer_hash)
            raise HTTPException(status_code=400, detail=msg)

        write_audit(store_root, AuditEvent(action="ingest.accept", bundle_id=cb.bundle_id, village_id=village_id, issuer_key_hash=issuer_hash, actor=member.get("member_id"), reason="accepted", policy_hash=policy_hash(v.policy.model_dump())))
        return {"status": "ok", "message": msg, "bundle_id": cb.bundle_id, "village_id": village_id}

    return app
