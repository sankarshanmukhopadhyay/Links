from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def validate_jsonl(model: Type[T], input_path: Path, output_path: Path) -> int:
    """
    Validates JSONL rows as `model` and writes normalized JSONL.
    Returns number of records written.
    """
    rows = read_jsonl(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with output_path.open("w", encoding="utf-8") as f:
        for row in rows:
            obj = model.model_validate(row)
            f.write(obj.model_dump_json() + "\n")
            n += 1
    return n
