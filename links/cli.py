from __future__ import annotations

from pathlib import Path
import json
import secrets
import typer
import requests

from links.server import create_app
from links.store import ingest_bundle_file, query_claims
from links.villages import (
    Village, VillageGovernance, VillagePolicy, save_village, load_village, save_village_policy,
    add_member, revoke_member, rotate_member_token,
    issuer_key_hash_from_public_key_b64, add_issuer_allow, add_issuer_block,
)
from links.quarantine import list_quarantine, approve_quarantine, reject_quarantine

app = typer.Typer(help="Links: verifiable claim exchange with group policy controls.")
villages_app = typer.Typer(help="Group governance and policy controls")
claims_app = typer.Typer(help="Store operations for bundles")
sync_app = typer.Typer(help="HTTP sync helpers")
quarantine_app = typer.Typer(help="Review workflow for quarantined bundles")

app.add_typer(villages_app, name="villages")
app.add_typer(claims_app, name="claims")
app.add_typer(sync_app, name="sync")
app.add_typer(quarantine_app, name="quarantine")


@villages_app.command("create")
def villages_create(
    village_id: str,
    name: str,
    admin: str,
    description: str = "",
    visibility: str = "village",
    allowed_predicate: str = "links.weighted_to",
    max_window_days: int = 30,
    require_issuer_allowlist: bool = False,
):
    v = Village(
        village_id=village_id,
        name=name,
        description=description,
        created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        governance=VillageGovernance(admins=[admin]),
        policy=VillagePolicy(
            visibility=visibility,
            allowed_predicates=[allowed_predicate],
            max_window_days=max_window_days,
            require_issuer_allowlist=require_issuer_allowlist,
        ),
    )
    p = save_village(Path("data"), v)
    token = secrets.token_urlsafe(32)
    add_member(Path("data"), village_id, member_id=admin, role="admin", token_plain=token, actor=admin)
    typer.echo(f"Created village at {p}")
    typer.echo("Admin bearer token (store securely, shown once):")
    typer.echo(token)


@villages_app.command("add-member")
def villages_add_member(village_id: str, member_id: str, role: str = "member", actor: str = "admin"):
    token = secrets.token_urlsafe(32)
    add_member(Path("data"), village_id, member_id=member_id, role=role, token_plain=token, actor=actor)
    typer.echo("Member bearer token (store securely, shown once):")
    typer.echo(token)


@villages_app.command("revoke-member")
def villages_revoke_member(village_id: str, member_id: str, actor: str = "admin", reason: str = "revoked"):
    n = revoke_member(Path("data"), village_id, member_id=member_id, actor=actor, reason=reason)
    typer.echo(f"Revoked {n} token(s) for member_id={member_id}")


@villages_app.command("rotate-token")
def villages_rotate_token(village_id: str, member_id: str, actor: str = "admin"):
    token = secrets.token_urlsafe(32)
    rotate_member_token(Path("data"), village_id, member_id=member_id, new_token_plain=token, actor=actor)
    typer.echo("New bearer token (store securely, shown once):")
    typer.echo(token)


@villages_app.command("allow-issuer")
def villages_allow_issuer(village_id: str, public_key_b64: str, actor: str = "admin"):
    kh = issuer_key_hash_from_public_key_b64(public_key_b64)
    add_issuer_allow(Path("data"), village_id, issuer_key_hash=kh, actor=actor)
    typer.echo(f"Allowed issuer key hash: {kh}")


@villages_app.command("block-issuer")
def villages_block_issuer(village_id: str, public_key_b64: str, actor: str = "admin"):
    kh = issuer_key_hash_from_public_key_b64(public_key_b64)
    add_issuer_block(Path("data"), village_id, issuer_key_hash=kh, actor=actor)
    typer.echo(f"Blocked issuer key hash: {kh}")


@villages_app.command("show")
def villages_show(village_id: str):
    v = load_village(Path("data"), village_id)
    typer.echo(v.model_dump_json(indent=2))


@claims_app.command("ingest")
def claims_ingest(inp: Path, store_root: Path = Path("data/store")):
    ok, msg = ingest_bundle_file(inp, store_root=store_root)
    typer.echo(msg)
    raise typer.Exit(code=0 if ok else 1)


@claims_app.command("query")
def claims_query(subject: str = None, issuer: str = None, predicate: str = None, village_id: str = None):
    rows = query_claims(subject=subject, issuer=issuer, predicate=predicate, village_id=village_id)
    typer.echo(json.dumps(rows, ensure_ascii=False, indent=2))


@sync_app.command("pull-village")
def pull_village(url: str, village_id: str, token: str, ingest: bool = True, inbox_dir: Path = Path("data/inbox")):
    endpoint = url.rstrip("/") + f"/villages/{village_id}/claims/latest"
    r = requests.get(endpoint, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    bundle = r.json()
    bundle_id = bundle.get("bundle_id", "unknown")
    inbox_dir.mkdir(parents=True, exist_ok=True)
    out = inbox_dir / f"{village_id}.{bundle_id}.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"Pulled village bundle {bundle_id} -> {out}")
    if ingest:
        ok, msg = ingest_bundle_file(out, store_root=Path("data/store"))
        typer.echo(msg)
        raise typer.Exit(code=0 if ok else 1)


@sync_app.command("push-village")
def push_village(url: str, village_id: str, token: str, bundle: Path):
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    endpoint = url.rstrip("/") + f"/villages/{village_id}/inbox"
    r = requests.post(endpoint, headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=30)
    if r.status_code >= 400:
        typer.echo(r.text)
        raise typer.Exit(code=1)
    typer.echo(r.text)


@quarantine_app.command("list")
def quarantine_list(village_id: str = None, store_root: Path = Path("data/store")):
    paths = list_quarantine(store_root, village_id=village_id)
    typer.echo("\n".join([str(p) for p in paths]) if paths else "(empty)")


@quarantine_app.command("approve")
def quarantine_approve(bundle_path: Path, store_root: Path = Path("data/store")):
    ok, msg = approve_quarantine(store_root, bundle_path)
    typer.echo(msg)
    raise typer.Exit(code=0 if ok else 1)


@quarantine_app.command("reject")
def quarantine_reject(bundle_path: Path, village_id: str = None, reason: str = "rejected", store_root: Path = Path("data/store")):
    ok, msg = reject_quarantine(store_root, bundle_path, village_id=village_id, reason=reason)
    typer.echo(msg)
    raise typer.Exit(code=0 if ok else 1)


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8080):
    import uvicorn
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    app()
