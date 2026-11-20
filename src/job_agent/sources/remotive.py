"""Remotive (remotive.com). Sus condiciones piden enlazar a la oferta original y citar a Remotive como fuente."""
from __future__ import annotations

from datetime import datetime, timezone

from ..models import Job, clean_html
from ..salary import parse_salary_text
from .base import get

API = "https://remotive.com/api/remote-jobs"
NAME = "Remotive"


def _locations(raw: str) -> list[str]:
    return [p.strip() for p in (raw or "").replace(";", ",").split(",") if p.strip()]


def parse(item: dict) -> Job:
    lo, hi = parse_salary_text(item.get("salary"))
    published = None
    if item.get("publication_date"):
        published = datetime.fromisoformat(item["publication_date"]).replace(tzinfo=timezone.utc)
    return Job(
        source=NAME,
        id=str(item["id"]),
        title=item.get("title", "").strip(),
        company=item.get("company_name", ""),
        url=item.get("url", ""),
        description=clean_html(item.get("description")),
        published=published,
        locations=_locations(item.get("candidate_required_location", "")),
        salary_min_usd=lo,
        salary_max_usd=hi,
        salary_text=item.get("salary") or "",
    )


def fetch(queries: list[str] | None = None) -> list[Job]:
    """Una sola llamada al feed completo: Remotive pide no consultar su API más de unas pocas veces al día."""
    return [parse(item) for item in get(API).json().get("jobs", [])]
