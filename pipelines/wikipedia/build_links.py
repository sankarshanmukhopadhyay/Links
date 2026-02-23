from __future__ import annotations

from pathlib import Path

from links.derive import build_links_file


def build_links(
    observations_path: Path = Path("data/normalized/observations.jsonl"),
    window_days: int = 30,
    edges_out: Path = Path("artifacts/graphs/wikipedia_admins_edges_30d.json"),
    graphml_out: Path = Path("artifacts/graphs/wikipedia_admins_30d.graphml"),
):
    return build_links_file(observations_path, edges_out, graphml_out, window_days=window_days)
