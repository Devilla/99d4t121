"""Tiny on-disk JSON cache.

Jan 2026 is fully in the past for both datasets we use: settled actuals
never change, and a forecast run's published values are a historical
record that is never revised. So once a window of data has been fetched
from Elexon it is safe to cache indefinitely -- this just avoids hitting
the public API on every request/container start.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable

_default_cache_dir = (
    "/tmp/elexon-wind-cache"
    if os.environ.get("VERCEL")
    else str(Path(__file__).resolve().parent.parent / ".cache")
)
CACHE_DIR = Path(os.environ.get("CACHE_DIR", _default_cache_dir))


def _key_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(key.encode()).hexdigest()[:24]
    return CACHE_DIR / f"{digest}.json"


def cached_fetch(key: str, fetch_fn: Callable[[], Any]) -> Any:
    path = _key_path(key)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass  # fall through and refetch
    data = fetch_fn()
    try:
        path.write_text(json.dumps(data))
    except OSError:
        pass  # cache is best-effort only (e.g. read-only serverless fs)
    return data
