#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from links.client import LinksClient

BASE_URL = "http://127.0.0.1:8000"
VILLAGE_ID = "demo"

def main():
    c = LinksClient(BASE_URL, token=None)
    man = c.policy_manifest(VILLAGE_ID)
    out = Path("snapshot.json")
    out.write_text(json.dumps(man, indent=2), encoding="utf-8")
    print("Wrote", out)

if __name__ == "__main__":
    main()
