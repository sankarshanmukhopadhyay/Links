from __future__ import annotations

from typing import Iterable, Any


def summarize(items: Iterable[Any]) -> str:
    items = list(items)
    if not items:
        return "empty"
    return f"{len(items)} items, first={items[0]}"
