from __future__ import annotations

from pathlib import Path
import json
import typer
import requests

from pipelines.wikipedia.ingest_admins import ingest_admins
from pipelines.wikipedia.ingest_mentions import ingest_user_talk_interactions
from pipelines.wikipedia.normalize import normalize_observations
from pipelines.wikipedia.build_links import build_links

from links.claims import build_bundle_from_edges, load_signing_key, read_bundle, sign_bundle, verify_bundle, write_bundle
from links.keys import generate_ed25519_keypair
from links.store import ingest_bundle_file, query_claims
from links.server import create_app

app = typer.Typer(help="Links: schema-backed pipelines + signed claim bundles for exchange.")
wikipedia_app = typer.Typer(help="Wikipedia pipelines (Phase 2)")
claims_app = typer.Typer(help="Claim bundles (Phase 3a/3b)")
sync_app = typer.Typer(help="HTTP sync (Phase 3c)")
keys_app = typer.Typer(help="Key management")

app.add_typer(wikipedia_app, name="wikipedia")
app.add_typer(claims_app, name="claims")
app.add_typer(sync_app, name="sync")
app.add_typer(keys_app, name="keys")


@wikipedia_app.command("run-all")
def wikipedia_run_all_cmd(
    limit: int = 200,
    active_days: int = 30,
    window_days: int = 30,
    per_user_limit: int = 200,
):
    admins_out = Path("data/raw/wikipedia_admins.jsonl")
    obs_raw = Path("data/raw/wikipedia_observations.jsonl")
    obs_norm = Path("data/normalized/observations.jsonl")

    ingest_admins(limit=limit, active_days=active_days, out_path=admins_out)
    ingest_user_talk_interactions(admins_path=admins_out, window_days=window_days, per_user_limit=per_user_limit, out_path=obs_raw)
    normalize_observations(input_path=obs_raw, output_path=obs_norm)
    build_links(observations_path=obs_norm, window_days=window_days)

    typer.echo("Phase 2 done. See artifacts/graphs/ for outputs.")


@keys_app.command("gen")
def keys_gen(out_dir: Path = Path("keys")):
    priv, pub = generate_ed25519_keypair(out_dir)
    typer.echo(f"Wrote private key seed to {priv}")
    typer.echo(f"Wrote public key to {pub}")


@claims_app.command("build")
def claims_build(
    edges: Path = Path("artifacts/graphs/wikipedia_admins_edges_30d.json"),
    issuer: str = "links-node:local",
    window_days: int = 30,
    out: Path = Path("artifacts/claims/claim_bundle.json"),
):
    bundle = build_bundle_from_edges(edges, issuer=issuer, window_days=window_days)
    write_bundle(out, bundle)
    typer.echo(f"Wrote unsigned bundle {bundle.bundle_id} with {len(bundle.claims)} claims to {out}")


@claims_app.command("sign")
def claims_sign(
    inp: Path = Path("artifacts/claims/claim_bundle.json"),
    key: Path = Path("keys/ed25519.key"),
    out: Path = Path("artifacts/claims/claim_bundle.signed.json"),
):
    bundle = read_bundle(inp)
    sk = load_signing_key(key)
    signed = sign_bundle(bundle, sk)
    write_bundle(out, signed)
    typer.echo(f"Signed bundle {signed.bundle_id} -> {out}")


@claims_app.command("verify")
def claims_verify(inp: Path = Path("artifacts/claims/claim_bundle.signed.json")):
    ok = verify_bundle(read_bundle(inp))
    typer.echo("OK" if ok else "FAIL")
    raise typer.Exit(code=0 if ok else 1)


@claims_app.command("ingest")
def claims_ingest(inp: Path, store_root: Path = Path("data/store")):
    ok, msg = ingest_bundle_file(inp, store_root=store_root)
    typer.echo(msg)
    raise typer.Exit(code=0 if ok else 1)


@claims_app.command("query")
def claims_query(subject: str = None, issuer: str = None, predicate: str = None):
    rows = query_claims(subject=subject, issuer=issuer, predicate=predicate)
    typer.echo(json.dumps(rows, ensure_ascii=False, indent=2))


@sync_app.command("pull")
def sync_pull(url: str, ingest: bool = True, inbox_dir: Path = Path("data/inbox")):
    endpoint = url.rstrip("/") + "/.well-known/links/claims/latest"
    r = requests.get(endpoint, timeout=30)
    r.raise_for_status()
    bundle = r.json()
    bundle_id = bundle.get("bundle_id", "unknown")
    inbox_dir.mkdir(parents=True, exist_ok=True)
    out = inbox_dir / f"{bundle_id}.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"Pulled bundle {bundle_id} -> {out}")
    if ingest:
        ok, msg = ingest_bundle_file(out, store_root=Path("data/store"))
        typer.echo(msg)
        raise typer.Exit(code=0 if ok else 1)


@sync_app.command("push")
def sync_push(url: str, bundle: Path = Path("artifacts/claims/claim_bundle.signed.json")):
    endpoint = url.rstrip("/") + "/inbox"
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    r = requests.post(endpoint, json=payload, timeout=30)
    if r.status_code >= 400:
        typer.echo(r.text)
        raise typer.Exit(code=1)
    typer.echo(r.text)


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8080):
    import uvicorn
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    app()
