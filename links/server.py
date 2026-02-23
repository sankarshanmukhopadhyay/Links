from __future__ import annotations

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header

from .claims import ClaimBundle, verify_bundle
from .store import ingest_bundle_file
from .villages import load_village, authorize, enforce_policy_on_bundle


def _latest_path(glob_it):
    candidates = sorted(list(glob_it), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def create_app(store_root: Path = Path("data/store"), inbox_root: Path = Path("data/inbox"), villages_root: Path = Path("data")) -> FastAPI:
    app = FastAPI(title="Links Claim Exchange", version="0.4.0")
    inbox_root.mkdir(parents=True, exist_ok=True)

    @app.get("/.well-known/links/claims/latest")
    def latest_bundle():
        p = _latest_path((store_root / "bundles").rglob("*.json")) if (store_root / "bundles").exists() else None
        if not p:
            raise HTTPException(status_code=404, detail="no bundles available")
        return json.loads(p.read_text(encoding="utf-8"))

    @app.get("/villages/{village_id}/claims/latest")
    def latest_village_bundle(village_id: str, authorization: str | None = Header(default=None)):
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
        if not token or not authorize(villages_root, village_id, token):
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
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
        member = authorize(villages_root, village_id, token) if token else None
        if not member:
            raise HTTPException(status_code=403, detail="forbidden")

        cb = ClaimBundle.model_validate(bundle)
        if not verify_bundle(cb):
            raise HTTPException(status_code=400, detail="invalid bundle (signature/bundle_id)")

        v = load_village(villages_root, village_id)
        okp, msgp = enforce_policy_on_bundle(v, bundle)
        if not okp:
            raise HTTPException(status_code=400, detail=f"policy violation: {msgp}")

        bundle["village_id"] = village_id
        bundle["visibility"] = "village"

        inbox_path = inbox_root / f"{village_id}.{cb.bundle_id}.json"
        inbox_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        ok, msg = ingest_bundle_file(inbox_path, store_root=store_root)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "ok", "message": msg, "bundle_id": cb.bundle_id, "village_id": village_id}

    return app
