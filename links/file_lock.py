from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

# POSIX-only lock via fcntl. This repo currently targets macOS/Linux style environments.
try:
    import fcntl  # type: ignore
except Exception:  # pragma: no cover
    fcntl = None


@contextmanager
def locked_open(path: Path, mode: str):
    """
    Open a file and hold an exclusive lock for the duration of the context.
    Intended for append/write of JSONL logs under multi-request or multi-worker conditions.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    f = path.open(mode, encoding="utf-8")
    try:
        if fcntl is not None:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        yield f
    finally:
        try:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()
