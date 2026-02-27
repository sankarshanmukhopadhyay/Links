from __future__ import annotations

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Query
import os
import base64
from nacl.signing import SigningKey

from .policy_updates import VillagePolicyUpdate, build_update
from .policy_feed import store_policy_update, latest_policy_update, filter_updates_since, signer_allowed, paginate_updates, list_policy_updates, build_policy_feed_manifest, sign_manifest
from .validate import validate_village_id

# Optional: if a richer villages module exists, use it for auth + apply.
try:
    from .villages import authorize, role_can, load_village, apply_policy_update  # type: ignore
except Exception:  # pragma: no cover
    authorize = None
    role_can = None
    load_village = None
    apply_policy_update = None


def _bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def create_app(store_root: Path = Path("data/store"), villages_root: Path = Path("data")) -> FastAPI:
    app = FastAPI(title="Links Claim Exchange", version="0.8.0")

    @app.get("/villages/{village_id}/policy/latest")
    def policy_latest(village_id: str):
        validate_village_id(village_id)
        u = latest_policy_update(villages_root, village_id)
        if not u:
            raise HTTPException(status_code=404, detail="no policy updates")
        return json.loads(u.model_dump_json())

    @app.get("/villages/{village_id}/policy/updates")
    def policy_updates(village_id: str, since: str | None = Query(default=None)):
        validate_village_id(village_id)
        ups = filter_updates_since(villages_root, village_id, since_hash=since)
        return [json.loads(u.model_dump_json()) for u in ups]

    
    @app.get("/villages/{village_id}/policy/updates_page")
    def policy_updates_page(
        village_id: str,
        since: str | None = Query(default=None),
        cursor: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ):
        """Paginated policy updates (envelope). Cursor is the last policy_hash from the previous page."""
        validate_village_id(village_id)
        ups = filter_updates_since(villages_root, village_id, since_hash=since)
        items, next_cursor = paginate_updates(ups, cursor=cursor, limit=limit)
        return {
            "village_id": village_id,
            "since": since,
            "cursor": cursor,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [json.loads(u.model_dump_json()) for u in items],
        }

    @app.get("/villages/{village_id}/policy/manifest")
    def policy_manifest(village_id: str):
        """Signed policy feed manifest with integrity metadata (merkle root + hash chain head)."""
        validate_village_id(village_id)
        m = build_policy_feed_manifest(villages_root, village_id)

        # Optional node signing key (base64 seed). If present, manifests are signed.
        sk_b64 = os.environ.get("LINKS_NODE_SIGNING_KEY_B64")
        if sk_b64:
            try:
                seed = base64.b64decode(sk_b64.strip())
                sk = SigningKey(seed[:32])
                m = sign_manifest(m, sk)
            except Exception:
                # Fail open (manifest still returned unsigned) to avoid breaking dev deployments.
                pass

        return json.loads(m.model_dump_json())
@app.post("/villages/{village_id}/policy")
    def policy_update(village_id: str, body: dict, authorization: str | None = Header(default=None)):
        validate_village_id(village_id)

        # If auth system exists, require manage permission.
        if authorize and role_can and load_village:
            token = _bearer_token(authorization)
            member = authorize(villages_root, village_id, token) if token else None
            if not member:
                raise HTTPException(status_code=403, detail="forbidden")
            v = load_village(villages_root, village_id)
            if not role_can(v.policy, member.get("role", "observer"), "manage"):
                raise HTTPException(status_code=403, detail="forbidden")
            current_policy = v.policy.model_dump()
            actor = member.get("member_id")
        else:
            # local/dev mode
            current_policy = {}
            actor = "local"

        # Accept either signed update artifact or raw policy dict
        try:
            u = VillagePolicyUpdate.model_validate(body)
        except Exception:
            policy_obj = body.get("policy") if isinstance(body, dict) and "policy" in body else body
            u = build_update(village_id=village_id, policy=policy_obj, actor=actor)

        ok, msg = signer_allowed(current_policy, u)
        if not ok:
            raise HTTPException(status_code=400, detail=f"policy update rejected: {msg}")

        store_policy_update(villages_root, u)

        # Apply locally if the implementation supports it
        if apply_policy_update:
            apply_policy_update(villages_root, village_id, u.policy, actor=actor, update_meta={"policy_hash": u.policy_hash, "policy_update": "stored"})
        return {"status": "ok", "village_id": village_id, "policy_hash": u.policy_hash}

    return app
