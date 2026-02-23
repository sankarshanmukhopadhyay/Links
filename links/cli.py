from __future__ import annotations

from pathlib import Path
import typer

from pipelines.wikipedia.ingest_admins import ingest_admins
from pipelines.wikipedia.ingest_mentions import ingest_user_talk_interactions
from pipelines.wikipedia.normalize import normalize_observations
from pipelines.wikipedia.build_links import build_links

app = typer.Typer(help="Links: schema-backed pipeline to derive explainable reputation graphs from public observations.")

wikipedia_app = typer.Typer(help="Wikipedia (enwiki) pipelines")
app.add_typer(wikipedia_app, name="wikipedia")


@wikipedia_app.command("admins")
def wikipedia_admins_cmd(
    limit: int = typer.Option(200, help="Max number of admins to sample."),
    active_days: int = typer.Option(30, help="Active if last edit within this many days."),
    out: Path = typer.Option(Path("data/raw/wikipedia_admins.jsonl"), help="Output JSONL path."),
):
    n = ingest_admins(limit=limit, active_days=active_days, out_path=out)
    typer.echo(f"Wrote {n} admin rows to {out}")


@wikipedia_app.command("mentions")
def wikipedia_mentions_cmd(
    window_days: int = typer.Option(30, help="Observation window in days."),
    per_user_limit: int = typer.Option(200, help="Max user talk contributions per admin to scan."),
    admins: Path = typer.Option(Path("data/raw/wikipedia_admins.jsonl"), help="Admins JSONL input."),
    out: Path = typer.Option(Path("data/raw/wikipedia_observations.jsonl"), help="Output observations JSONL."),
):
    n = ingest_user_talk_interactions(admins_path=admins, window_days=window_days, per_user_limit=per_user_limit, out_path=out)
    typer.echo(f"Wrote {n} raw observations to {out}")


@wikipedia_app.command("normalize")
def wikipedia_normalize_cmd(
    inp: Path = typer.Option(Path("data/raw/wikipedia_observations.jsonl"), help="Raw observations JSONL input."),
    out: Path = typer.Option(Path("data/normalized/observations.jsonl"), help="Normalized observations JSONL output."),
):
    n = normalize_observations(input_path=inp, output_path=out)
    typer.echo(f"Validated and wrote {n} normalized observations to {out}")


@wikipedia_app.command("build-links")
def wikipedia_build_links_cmd(
    window_days: int = typer.Option(30, help="Window in days (metadata + derivation context)."),
    observations: Path = typer.Option(Path("data/normalized/observations.jsonl"), help="Normalized observations JSONL."),
    edges_out: Path = typer.Option(Path("artifacts/graphs/wikipedia_admins_edges_30d.json"), help="Edges JSON output."),
    graphml_out: Path = typer.Option(Path("artifacts/graphs/wikipedia_admins_30d.graphml"), help="GraphML output for Gephi."),
):
    links = build_links(observations_path=observations, window_days=window_days, edges_out=edges_out, graphml_out=graphml_out)
    typer.echo(f"Built {len(links)} links. Wrote edges to {edges_out} and graphml to {graphml_out}")


@wikipedia_app.command("run-all")
def wikipedia_run_all_cmd(
    limit: int = typer.Option(200),
    active_days: int = typer.Option(30),
    window_days: int = typer.Option(30),
    per_user_limit: int = typer.Option(200),
):
    admins_out = Path("data/raw/wikipedia_admins.jsonl")
    obs_raw = Path("data/raw/wikipedia_observations.jsonl")
    obs_norm = Path("data/normalized/observations.jsonl")

    ingest_admins(limit=limit, active_days=active_days, out_path=admins_out)
    ingest_user_talk_interactions(admins_path=admins_out, window_days=window_days, per_user_limit=per_user_limit, out_path=obs_raw)
    normalize_observations(input_path=obs_raw, output_path=obs_norm)
    build_links(observations_path=obs_norm, window_days=window_days)

    typer.echo("Done. See artifacts/graphs/ for outputs.")


if __name__ == "__main__":
    app()
