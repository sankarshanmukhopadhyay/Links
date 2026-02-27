from __future__ import annotations

from pathlib import Path
import json
import base64
import typer
import requests

from nacl.signing import SigningKey

from links.server import create_app
from links.policy_updates import VillagePolicyUpdate, verify_update_any, add_signature, sign_update_legacy, build_update
from links.policy_diff import diff_policies
from links.policy_feed import PolicyFeedManifest, verify_manifest
from links.reconcile import reconcile
from links.trust_anchors import TrustAnchorEntry, add_anchor_signature, verify_anchor_entry_any
from links.policy_feed import signer_allowed
from links.validate import validate_village_id

try:
    from links.villages import apply_policy_update, load_village  # type: ignore
except Exception:  # pragma: no cover
    apply_policy_update = None
    load_village = None

app = typer.Typer(help="Links: verifiable claim exchange with group policy controls.")
policy = typer.Typer(help="Policy feed operations")
anchors = typer.Typer(help="Trust anchor registry operations")
app.add_typer(policy, name="policy")
app.add_typer(anchors, name="anchors")


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8080):
    import ipaddress
    import uvicorn

    # Operational hardening: if you bind to a non-loopback interface, assume you're behind TLS termination.
    try:
        ip = ipaddress.ip_address(host)
        is_loopback = ip.is_loopback
    except Exception:
        is_loopback = host in ("localhost", "127.0.0.1", "::1")

    if not is_loopback:
        typer.echo("WARNING: Binding to a non-loopback interface. Run Links behind a TLS terminator (e.g., Nginx/Envoy) and use proper auth/rate limiting.", err=True)

    uvicorn.run(create_app(), host=host, port=port)


@policy.command("sign-add")
def policy_sign_add(inp: Path, key: Path, out: Path):
    """
    Append a signer signature to a policy update artifact (multisig quorum).
    """
    u = VillagePolicyUpdate.model_validate_json(inp.read_text(encoding="utf-8"))
    seed = base64.b64decode(key.read_text(encoding="utf-8").strip())
    sk = SigningKey(seed[:32])
    s = add_signature(u, sk)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")


@policy.command("sign-legacy")
def policy_sign_legacy(inp: Path, key: Path, out: Path):
    """
    Produce a legacy single-signature policy update (public_key + signature).
    """
    u = VillagePolicyUpdate.model_validate_json(inp.read_text(encoding="utf-8"))
    seed = base64.b64decode(key.read_text(encoding="utf-8").strip())
    sk = SigningKey(seed[:32])
    s = sign_update_legacy(u, sk)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")


@policy.command("verify")
def policy_verify(inp: Path):
    u = VillagePolicyUpdate.model_validate_json(inp.read_text(encoding="utf-8"))
    ok = verify_update_any(u)
    typer.echo("OK" if ok else "FAIL")
    raise typer.Exit(code=0 if ok else 1)


@policy.command("pull")
def policy_pull(url: str, village_id: str, apply: bool = True, since: str = None, token: str = None, page_limit: int = 200):
    """
    Pull policy updates from a remote node using:
      1) Signed manifest (if available)
      2) Paginated updates (large-history optimization)

    Reconcile rule (default): select latest update by (created_at, policy_hash).
    Also prints fork detection signals when previous_policy_hash links diverge.
    """
    validate_village_id(village_id)
    base = url.rstrip("/")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 1) Fetch manifest (optional but preferred)
    manifest = None
    try:
        mr = requests.get(f"{base}/villages/{village_id}/policy/manifest", headers=headers, timeout=30)
        if mr.status_code == 200:
            manifest = mr.json()
    except Exception:
        manifest = None

    # 2) Fetch updates (paginated if supported)
    updates = []
    try:
        cursor = None
        while True:
            pr = requests.get(
                f"{base}/villages/{village_id}/policy/updates_page",
                params={"since": since, "cursor": cursor, "limit": page_limit},
                headers=headers,
                timeout=30,
            )
            if pr.status_code != 200:
                raise RuntimeError("updates_page not supported")
            payload = pr.json()
            updates.extend([VillagePolicyUpdate.model_validate(u) for u in payload.get("items", [])])
            cursor = payload.get("next_cursor")
            if not cursor:
                break
    except Exception:
        # fallback: legacy endpoint
        endpoint = f"{base}/villages/{village_id}/policy/updates"
        params = {}
        if since:
            params["since"] = since
        r = requests.get(endpoint, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        updates = [VillagePolicyUpdate.model_validate(u) for u in r.json()]

    if not updates:
        typer.echo("No updates.")
        raise typer.Exit(code=0)

    # Verify signature material (if any) for each update.
    for u in updates:
        has_any = bool(u.signatures) or bool(u.public_key) or bool(u.signature)
        if has_any and not verify_update_any(u):
            typer.echo(f"Invalid signature material for update policy_hash={u.policy_hash}")
            raise typer.Exit(code=1)

    # Reconcile: choose latest
    updates.sort(key=lambda u: (u.created_at, u.policy_hash), reverse=True)
    chosen = updates[0]

    # Drift detection (best-effort)
    local_hash = None
    if load_village:
        try:
            v = load_village(Path("data"), village_id)
            local_hash = __import__("links.policy_updates", fromlist=["compute_policy_hash"]).compute_policy_hash(v.policy.model_dump())
        except Exception:
            local_hash = None

    if local_hash and local_hash != chosen.policy_hash:
        typer.echo(f"Drift detected: local={local_hash} remote_latest={chosen.policy_hash}")
    else:
        typer.echo(f"Remote latest policy_hash={chosen.policy_hash}")

    # Fork detection (best-effort)
    try:
        from links.reconcile import detect_forks
        forks = detect_forks(updates)
        if forks:
            typer.echo(f"Fork signals detected: {len(forks)} (run `links policy reconcile` for full report)")
    except Exception:
        pass

    if apply and apply_policy_update:
        current_policy = {}
        if load_village:
            try:
                v = load_village(Path('data'), village_id)
                current_policy = v.policy.model_dump()
            except Exception:
                current_policy = {}
        ok, msg = signer_allowed(current_policy, chosen)
        if not ok:
            typer.echo(f"Refusing to apply update: {msg}")
            raise typer.Exit(code=1)

        apply_policy_update(Path("data"), village_id, chosen.policy, actor=chosen.actor or "pull", update_meta={"policy_hash": chosen.policy_hash, "policy_update": "pull"})
        typer.echo("Applied.")
    else:
        typer.echo("Not applied (apply=false or local apply not available).")

    out_dir = Path("artifacts/policy_feed") / village_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"latest.{chosen.policy_hash}.json"
    out.write_text(chosen.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")

@policy.command("drift")
def policy_drift(url: str, village_id: str, token: str = None):
    """
    Compare local policy hash to remote latest policy hash.
    """
    validate_village_id(village_id)
    base = url.rstrip("/")
    endpoint = f"{base}/villages/{village_id}/policy/latest"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(endpoint, headers=headers, timeout=30)
    r.raise_for_status()
    remote = VillagePolicyUpdate.model_validate(r.json())
    remote_hash = remote.policy_hash

    local_hash = None
    if load_village:
        try:
            v = load_village(Path("data"), village_id)
            local_hash = __import__("links.policy_updates", fromlist=["compute_policy_hash"]).compute_policy_hash(v.policy.model_dump())
        except Exception:
            local_hash = None

    typer.echo(json.dumps({"village_id": village_id, "local_policy_hash": local_hash, "remote_policy_hash": remote_hash, "drift": (local_hash != remote_hash)}, indent=2))
