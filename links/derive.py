from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Iterable

import networkx as nx

from .io import read_jsonl, write_jsonl
from .models import Observation


def build_links_from_observations(observations: Iterable[dict], window_days: int = 30) -> list[dict]:
    """
    Derives directed links from observations.
    Current MVP: kind == "user_talk_edit" edges actor -> target, weight = log(1 + count).
    """
    counts: Counter[tuple[str, str]] = Counter()
    for row in observations:
        obs = Observation.model_validate(row)
        if obs.kind != "user_talk_edit":
            continue
        if not obs.target_entity_id:
            continue
        counts[(obs.actor_entity_id, obs.target_entity_id)] += 1

    links: list[dict] = []
    for (src, dst), c in sorted(counts.items()):
        links.append({
            "from_entity_id": src,
            "to_entity_id": dst,
            "weight": float(math.log1p(c)),
            "window_days": int(window_days),
            "derivation": "log(1 + count_30d)"
        })
    return links


def export_graph_json(links: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dumps_pretty(links), encoding="utf-8")


def json_dumps_pretty(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def export_graph_graphml(links: list[dict], path: Path) -> None:
    G = nx.DiGraph()
    for e in links:
        G.add_edge(e["from_entity_id"], e["to_entity_id"], weight=e["weight"])
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, path)


def build_links_file(observations_jsonl: Path, out_edges_json: Path, out_graphml: Path | None, window_days: int = 30) -> list[dict]:
    observations = read_jsonl(observations_jsonl)
    links = build_links_from_observations(observations, window_days=window_days)
    export_graph_json(links, out_edges_json)
    if out_graphml is not None:
        export_graph_graphml(links, out_graphml)
    return links
