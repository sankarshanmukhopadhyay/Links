from __future__ import annotations

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

from .claims import ClaimBundle, verify_bundle
from .store import ingest_bundle_file


def create_app(store_root: Path = Path("data/store"), inbox_root: Path = Path("data/inbox")) -> FastAPI:
    app = FastAPI(title="Links Claim Exchange", version="0.3.0")
    inbox_root.mkdir(parents=True, exist_ok=True)

    @app.get("/.well-known/links/claims/latest")
    def latest_bundle():
        bundles_dir = store_root / "bundles"
        if not bundles_dir.exists():
            raise HTTPException(status_code=404, detail="no bundles available")
        candidates = sorted(bundles_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise HTTPException(status_code=404, detail="no bundles available")
        return json.loads(candidates[0].read_text(encoding="utf-8"))

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

    return app
