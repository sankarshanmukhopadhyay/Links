from __future__ import annotations

from pathlib import Path

from links.io import validate_jsonl
from links.models import Observation


def normalize_observations(
    input_path: Path = Path("data/raw/wikipedia_observations.jsonl"),
    output_path: Path = Path("data/normalized/observations.jsonl"),
) -> int:
    return validate_jsonl(Observation, input_path, output_path)
