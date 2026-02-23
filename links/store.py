from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Iterable

from .claims import ClaimBundle, verify_bundle, iso_utc


def ensure_dirs(store_root: Path) -> None:
    (store_root / "bundles").mkdir(parents=True, exist_ok=True)
    (store_root / "index").mkdir(parents=True, exist_ok=True)


def ingest_bundle_file(bundle_path: Path, store_root: Path = Path("data/store")) -> tuple[bool, str]:
    bundle = ClaimBundle.model_validate_json(bundle_path.read_text(encoding="utf-8"))
    if not verify_bundle(bundle):
        return False, "bundle failed verification (signature and/or bundle_id mismatch)"
    ensure_dirs(store_root)
    bundle_out = store_root / "bundles" / f"{bundle.bundle_id}.json"
    bundle_out.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")

    idx = store_root / "index" / "claims.jsonl"
    n = 0
    with idx.open("a", encoding="utf-8") as f:
        for c in bundle.claims:
            row = {
                "bundle_id": bundle.bundle_id,
                "issuer": bundle.issuer,
                "window_days": bundle.window_days,
                "created_at": iso_utc(bundle.created_at),
                **c.model_dump(),
                "computed_at": iso_utc(c.computed_at),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return True, f"ingested bundle {bundle.bundle_id} with {n} claims"


def iter_claim_rows(store_root: Path = Path("data/store")) -> Iterable[dict]:
    idx = store_root / "index" / "claims.jsonl"
    if not idx.exists():
        return []
    def _gen():
        with idx.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
    return _gen()


def query_claims(subject: Optional[str] = None, issuer: Optional[str] = None, predicate: Optional[str] = None, store_root: Path = Path("data/store")) -> list[dict]:
    out = []
    for row in iter_claim_rows(store_root):
        if subject and row.get("subject") != subject:
            continue
        if issuer and row.get("issuer") != issuer:
            continue
        if predicate and row.get("predicate") != predicate:
            continue
        out.append(row)
    return out
