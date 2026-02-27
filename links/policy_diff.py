from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .policy_updates import PolicyChangeSummary


def _is_primitive(x: Any) -> bool:
    return x is None or isinstance(x, (str, int, float, bool))


def _join(ptr: str, key: str) -> str:
    # JSON Pointer encoding: ~ -> ~0, / -> ~1
    key = key.replace("~", "~0").replace("/", "~1")
    if ptr == "":
        return "/" + key
    return ptr + "/" + key


def _diff(old: Any, new: Any, ptr: str, added: List[str], removed: List[str], changed: List[str]) -> None:
    if old is None and new is None:
        return
    if old is None and new is not None:
        added.append(ptr or "/")
        return
    if old is not None and new is None:
        removed.append(ptr or "/")
        return

    if _is_primitive(old) or _is_primitive(new):
        if old != new:
            changed.append(ptr or "/")
        return

    if isinstance(old, list) and isinstance(new, list):
        # Treat list as changed if not identical. (We avoid heavy diff deps.)
        if old != new:
            changed.append(ptr or "/")
        return

    if isinstance(old, dict) and isinstance(new, dict):
        old_keys = set(old.keys())
        new_keys = set(new.keys())
        for k in sorted(new_keys - old_keys):
            added.append(_join(ptr, str(k)))
        for k in sorted(old_keys - new_keys):
            removed.append(_join(ptr, str(k)))
        for k in sorted(old_keys & new_keys):
            _diff(old.get(k), new.get(k), _join(ptr, str(k)), added, removed, changed)
        return

    # Fallback type mismatch
    if old != new:
        changed.append(ptr or "/")


def diff_policies(old_policy: Dict[str, Any], new_policy: Dict[str, Any]) -> PolicyChangeSummary:
    added: List[str] = []
    removed: List[str] = []
    changed: List[str] = []
    _diff(old_policy, new_policy, "", added, removed, changed)
    # de-dupe while preserving order
    def dedupe(xs: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in xs:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out
    return PolicyChangeSummary(added=dedupe(added), removed=dedupe(removed), changed=dedupe(changed))
