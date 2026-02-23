from __future__ import annotations

from pathlib import Path
import json
import typer
import requests

from links.server import create_app
from links.policy_updates import VillagePolicyUpdate, verify_update
from links.policy_feed import signer_allowed
from links.validate import validate_village_id

try:
    from links.villages import apply_policy_update, load_village  # type: ignore
except Exception:  # pragma: no cover
    apply_policy_update = None
    load_village = None

app = typer.Typer(help="Links: verifiable claim exchange with group policy controls.")
policy = typer.Typer(help="Policy feed operations")
app.add_typer(policy, name="policy")


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8080):
    import uvicorn
    uvicorn.run(create_app(), host=host, port=port)


@policy.command("pull")
def policy_pull(url: str, village_id: str, apply: bool = True, since: str = None, token: str = None):
    """
    Pull signed policy updates from a remote node, verify/reconcile, and optionally apply.
    Reconcile rule: select latest update by (created_at, policy_hash).
    """
    validate_village_id(village_id)
    base = url.rstrip("/")
    endpoint = f"{base}/villages/{village_id}/policy/updates"
    params = {}
    if since:
        params["since"] = since

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.get(endpoint, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    updates = [VillagePolicyUpdate.model_validate(u) for u in r.json()]

    if not updates:
        typer.echo("No updates.")
        raise typer.Exit(code=0)

    # verify signatures when present
    for u in updates:
        if u.public_key or u.signature:
            if not verify_update(u):
                typer.echo(f"Invalid signature for update policy_hash={u.policy_hash}")
                raise typer.Exit(code=1)

    updates.sort(key=lambda u: (u.created_at, u.policy_hash), reverse=True)
    chosen = updates[0]

    # drift detection
    local_hash = None
    if load_village:
        try:
            v = load_village(Path("data"), village_id)
            local_hash = getattr(v, "policy", None) and __import__("links.policy_updates", fromlist=["compute_policy_hash"]).compute_policy_hash(v.policy.model_dump())
        except Exception:
            local_hash = None

    if local_hash and local_hash != chosen.policy_hash:
        typer.echo(f"Drift detected: local={local_hash} remote_latest={chosen.policy_hash}")
    else:
        typer.echo(f"Remote latest policy_hash={chosen.policy_hash}")

    if apply and apply_policy_update:
        # enforce local signer policy if possible
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

    # Write a local copy of chosen update
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
