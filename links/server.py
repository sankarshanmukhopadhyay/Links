from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Dict, Tuple

from fastapi import FastAPI, Header, HTTPException, Query, Request
from nacl.signing import SigningKey

from .policy_feed import (
    build_policy_feed_manifest,
    filter_updates_since,
    latest_policy_update,
    paginate_updates,
    sign_manifest,
    signer_allowed,
    store_policy_update,
)
from .policy_updates import VillagePolicyUpdate, build_update
from .validate import validate_village_id

# Optional: if a richer villages module exists, use it for auth + apply + policy lookup.
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
    app = FastAPI(title="Links Claim Exchange", version="0.10.0")

    # Simple in-memory per-village rate limiter (minute bucket).
    # NOTE: In production, put Links behind a proper gateway (Envoy/Nginx) with real rate limiting.
    _buckets: Dict[Tuple[str, str], Tuple[int, int]] = {}  # (village_id, client_key) -> (minute_epoch, count)

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        path = request.url.path or ""
        # Only apply rate limiting to village-scoped routes.
        if path.startswith("/villages/"):
            parts = path.split("/")
            if len(parts) >= 3:
                village_id = parts[2]
                try:
                    validate_village_id(village_id)
                except Exception:
                    raise HTTPException(status_code=400, detail="invalid village_id")

                limit = 60
                if load_village:
                    try:
                        v = load_village(villages_root, village_id)
                        limit = int(getattr(v, "policy").rate_limit_per_min)  # type: ignore[attr-defined]
                    except Exception:
                        # Fail open to avoid breaking local/dev deployments.
                        limit = 60

                client_host = request.client.host if request.client else "unknown"
                client_key = client_host

                minute = int(time.time() // 60)
                k = (village_id, client_key)
                m0, c0 = _buckets.get(k, (minute, 0))
                if m0 != minute:
                    m0, c0 = minute, 0
                c0 += 1
                _buckets[k] = (m0, c0)

                # Opportunistic cleanup to keep memory bounded.
                if len(_buckets) > 5000:
                    cutoff = minute - 5
                    for kk, (mm, _) in list(_buckets.items()):
                        if mm < cutoff:
                            _buckets.pop(kk, None)

                if c0 > max(1, limit):
                    raise HTTPException(status_code=429, detail="rate limit exceeded")
        return await call_next(request)

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
                seed = base64.b64decode(sk_b64.strip(), validate=True)
                if len(seed) < 32:
                    raise ValueError("seed too short")
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
            apply_policy_update(
                villages_root,
                village_id,
                u.policy,
                actor=actor,
                update_meta={"policy_hash": u.policy_hash, "policy_update": "stored"},
            )
        return {"status": "ok", "village_id": village_id, "policy_hash": u.policy_hash}

    return app
