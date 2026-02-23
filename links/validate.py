from __future__ import annotations
import re

_VILLAGE_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

def validate_village_id(village_id: str) -> str:
    if not _VILLAGE_RE.fullmatch(village_id or ""):
        raise ValueError("invalid village_id (allowed: letters, numbers, underscore, hyphen)")
    return village_id
