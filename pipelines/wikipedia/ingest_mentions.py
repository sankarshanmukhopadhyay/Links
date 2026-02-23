from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Set
import hashlib

import pywikibot

from links.io import read_jsonl, write_jsonl


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(parts: list[str]) -> str:
    h = hashlib.sha256(("|".join(parts)).encode("utf-8")).hexdigest()
    return h[:32]


def ingest_user_talk_interactions(
    admins_path: Path = Path("data/raw/wikipedia_admins.jsonl"),
    window_days: int = 30,
    per_user_limit: int = 200,
    out_path: Path = Path("data/raw/wikipedia_observations.jsonl"),
) -> int:
    """
    MVP interaction definition (transparent + cheap):
      If admin A edits the User talk page of admin B within window_days,
      emit observation kind="user_talk_edit" with edge A -> B.

    This avoids diff parsing and is still a meaningful, publicly-observable interaction signal.
    """
    site = pywikibot.Site("en", "wikipedia")
    rows = read_jsonl(admins_path)

    admin_usernames: Set[str] = {r["username"] for r in rows if r.get("is_active")}
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    observations = []
    n = 0

    for username in sorted(admin_usernames):
        user = pywikibot.User(site, username)
        try:
            contribs = user.contributions(total=per_user_limit, namespaces=[3])  # namespace 3 = User talk
        except TypeError:
            # Older pywikibot might not support namespaces kw; fallback to namespace param
            contribs = user.contributions(total=per_user_limit, namespace=3)

        for page, revid, ts, comment in contribs:
            # timestamps may be pywikibot.Timestamp
            if isinstance(ts, datetime):
                ts_utc = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
            else:
                ts_utc = datetime.fromisoformat(str(ts)).astimezone(timezone.utc)

            if ts_utc < cutoff:
                continue

            title = getattr(page, "title", lambda: str(page))()
            # Expected: "User talk:TargetName"
            if not title.startswith("User talk:"):
                continue
            target = title.split("User talk:", 1)[1].strip()
            if not target or target == username:
                continue
            if target not in admin_usernames:
                continue

            evidence_uri = f"https://en.wikipedia.org/w/index.php?title={title.replace(' ', '_')}&oldid={revid}"
            obs_id = _stable_id([username, target, str(revid), _iso(ts_utc)])

            observations.append({
                "observation_id": obs_id,
                "timestamp": _iso(ts_utc),
                "actor_entity_id": f"wikipedia:en:{username}",
                "target_entity_id": f"wikipedia:en:{target}",
                "context": title,
                "kind": "user_talk_edit",
                "evidence_uri": evidence_uri,
            })
            n += 1

    write_jsonl(out_path, observations)
    return n
