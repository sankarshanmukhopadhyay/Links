from pathlib import Path
import json

from links.file_lock import locked_open


def test_locked_open_appends(tmp_path):
    p = tmp_path / "x.jsonl"
    with locked_open(p, "a") as f:
        f.write(json.dumps({"a":1}) + "\n")
    with locked_open(p, "a") as f:
        f.write(json.dumps({"b":2}) + "\n")
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
