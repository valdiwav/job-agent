"""Himalayas (himalayas.app): ofertas remotas con restricciones de país explícitas."""
from __future__ import annotations

from datetime import datetime, timezone

from ..models import Job, clean_html
from ..salary import to_monthly
from .base import get

API = "https://himalayas.app/jobs/api/search"
NAME = "Himalayas"


def _num(v) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def parse(item: dict) -> Job:
    period = item.get("salaryPeriod")
    smin, smax = _num(item.get("minSalary")), _num(item.get("maxSalary"))
    usd = (item.get("currency") or "USD").upper() == "USD"
    published = datetime.fromtimestamp(int(item["pubDate"]), tz=timezone.utc) if item.get("pubDate") else None
    return Job(
        source=NAME,
        id=item.get("guid") or item.get("applicationLink") or item["title"],
        title=(item.get("title") or "").strip(),
        company=item.get("companyName", ""),
        url=item.get("applicationLink") or item.get("guid", ""),
        description=clean_html(item.get("description") or item.get("excerpt")),
        published=published,
        locations=list(item.get("locationRestrictions") or []),
        salary_min_usd=to_monthly(smin, period) if smin and usd else None,
        salary_max_usd=to_monthly(smax, period) if smax and usd else None,
        salary_text=f"{item.get('currency', '')} {smin or ''}–{smax or ''} ({period})" if smin else "",
    )


def fetch(queries: list[str]) -> list[Job]:
    jobs: dict[str, Job] = {}
    for q in queries:
        r = get(API, {"q": q})
        for item in r.json().get("jobs", []):
            job = parse(item)
            jobs[job.id] = job
    return list(jobs.values())
