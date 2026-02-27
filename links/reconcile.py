from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple, Set

from .policy_updates import VillagePolicyUpdate, compute_update_hash


@dataclass
class ReconciliationReport:
    village_id: str
    local_head: Optional[str]
    remote_head: Optional[str]
    drift: bool
    forks: List[Dict[str, Any]]
    missing_local: List[str]
    missing_remote: List[str]


def _index_by_hash(ups: List[VillagePolicyUpdate]) -> Dict[str, VillagePolicyUpdate]:
    return {u.policy_hash: u for u in ups}


def detect_forks(ups: List[VillagePolicyUpdate]) -> List[Dict[str, Any]]:
    """Detect forks where multiple updates point to the same previous_policy_hash."""
    by_prev: Dict[Optional[str], List[VillagePolicyUpdate]] = {}
    for u in ups:
        by_prev.setdefault(u.previous_policy_hash, []).append(u)

    forks: List[Dict[str, Any]] = []
    for prev, children in by_prev.items():
        if prev is None:
            continue
        # multiple distinct policy_hash implies fork
        uniq = {c.policy_hash for c in children}
        if len(uniq) > 1:
            forks.append({
                "previous_policy_hash": prev,
                "children": sorted([
                    {
                        "policy_hash": c.policy_hash,
                        "created_at": c.created_at.isoformat(),
                        "update_hash": compute_update_hash(c),
                        "lifecycle_state": c.lifecycle_state,
                    } for c in children
                ], key=lambda x: (x["created_at"], x["policy_hash"])),
            })
    return forks


def reconcile(local: List[VillagePolicyUpdate], remote: List[VillagePolicyUpdate], village_id: str) -> ReconciliationReport:
    local_set = {u.policy_hash for u in local}
    remote_set = {u.policy_hash for u in remote}

    local_head = max(local, key=lambda u: (u.created_at, u.policy_hash)).policy_hash if local else None
    remote_head = max(remote, key=lambda u: (u.created_at, u.policy_hash)).policy_hash if remote else None

    forks = detect_forks(local + remote)

    return ReconciliationReport(
        village_id=village_id,
        local_head=local_head,
        remote_head=remote_head,
        drift=(local_head != remote_head),
        forks=forks,
        missing_local=sorted(list(remote_set - local_set)),
        missing_remote=sorted(list(local_set - remote_set)),
    )
