from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pywikibot

from links.io import write_jsonl


@dataclass(frozen=True)
class AdminRow:
    username: str
    last_edit: str  # ISO-8601 UTC
    is_active: bool


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _last_edit_utc(user: pywikibot.User) -> datetime | None:
    """
    Best-effort: fetch most recent contribution timestamp.
    """
    try:
        # contributions() yields tuples; timestamp is typically at index 2
        contribs = user.contributions(total=1)
        for _page, _revid, ts, _comment in contribs:
            # pywikibot timestamps may be pywikibot.Timestamp, compatible with datetime
            if isinstance(ts, datetime):
                return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
            # fallback: try to parse string
            return datetime.fromisoformat(str(ts)).astimezone(timezone.utc)
    except Exception:
        return None
    return None


def ingest_admins(limit: int = 200, active_days: int = 30, out_path: Path = Path("data/raw/wikipedia_admins.jsonl")) -> int:
    """
    Pull a limited sample of enwiki sysops (admins) and mark them active if last edit within active_days.
    """
    site = pywikibot.Site("en", "wikipedia")
    cutoff = datetime.now(timezone.utc) - timedelta(days=active_days)

    rows = []
    n = 0
    for u in site.allusers(group="sysop"):
        if n >= limit:
            break
        user = pywikibot.User(site, u["name"])
        last = _last_edit_utc(user)
        if last is None:
            last = datetime.fromtimestamp(0, tz=timezone.utc)
        rows.append({
            "username": u["name"],
            "last_edit": _iso(last),
            "is_active": bool(last >= cutoff),
        })
        n += 1

    write_jsonl(out_path, rows)
    return n
