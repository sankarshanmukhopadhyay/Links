"""Small example utility."""

def summarize(items):
    items = list(items)
    if not items:
        return "empty"
    return f"{len(items)} items, first={items[0]!r}"
