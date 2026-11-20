"""Remote OK (remoteok.com). Sus condiciones piden enlazar a la oferta y citar a Remote OK como fuente."""
from __future__ import annotations

from datetime import datetime, timezone

from ..models import Job, clean_html
from ..salary import to_monthly
from .base import get

API = "https://remoteok.com/api"
NAME = "Remote OK"


def parse(item: dict) -> Job:
    smin, smax = item.get("salary_min") or None, item.get("salary_max") or None
    published = datetime.fromtimestamp(int(item["epoch"]), tz=timezone.utc) if item.get("epoch") else None
    location = (item.get("location") or "").strip()
    return Job(
        source=NAME,
        id=str(item["id"]),
        title=(item.get("position") or "").strip(),
        company=item.get("company", ""),
        url=item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('slug', item['id'])}",
        description=clean_html(item.get("description")) + " " + " ".join(item.get("tags") or []),
        published=published,
        locations=[location] if location else [],
        salary_min_usd=to_monthly(float(smin), "year") if smin else None,  # Remote OK publica sueldos anuales
        salary_max_usd=to_monthly(float(smax), "year") if smax else None,
        salary_text=f"USD {smin:,}–{smax:,}/año" if smin and smax else "",
    )


def fetch(queries: list[str] | None = None) -> list[Job]:
    """Remote OK no filtra por texto: descarga el feed completo y el filtro local hace el resto."""
    data = get(API).json()
    return [parse(item) for item in data if isinstance(item, dict) and item.get("id")]
