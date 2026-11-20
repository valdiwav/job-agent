"""Registro de ofertas ya enviadas, para no repetirlas. En GitHub Actions se conserva con actions/cache."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

KEEP_DAYS = 60


def load(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save(path: Path, seen: dict[str, str], new_keys: list[str]) -> None:
    now = datetime.now(timezone.utc)
    for k in new_keys:
        seen[k] = now.isoformat()
    cutoff = now - timedelta(days=KEEP_DAYS)
    seen = {k: v for k, v in seen.items() if datetime.fromisoformat(v) >= cutoff}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, indent=0, sort_keys=True), encoding="utf-8")
