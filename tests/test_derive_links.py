import math
from pathlib import Path

from links.io import read_jsonl
from links.derive import build_links_from_observations


def test_build_links_deterministic():
    obs = read_jsonl(Path("tests/fixtures/observations.jsonl"))
    links = build_links_from_observations(obs, window_days=30)
    # Alice->Bob count=2 => log1p(2)
    ab = next(e for e in links if e["from_entity_id"]=="wikipedia:en:Alice" and e["to_entity_id"]=="wikipedia:en:Bob")
    assert abs(ab["weight"] - math.log1p(2)) < 1e-9
    # Bob->Alice count=1 => log1p(1)
    ba = next(e for e in links if e["from_entity_id"]=="wikipedia:en:Bob" and e["to_entity_id"]=="wikipedia:en:Alice")
    assert abs(ba["weight"] - math.log1p(1)) < 1e-9
