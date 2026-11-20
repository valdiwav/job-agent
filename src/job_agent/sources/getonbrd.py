"""Get on Board (getonbrd.com): la bolsa tech más usada en Chile y Latinoamérica. Sueldos en USD mensuales."""
from __future__ import annotations

from datetime import datetime, timezone

from ..models import Job, clean_html
from .base import get

API = "https://www.getonbrd.com/api/v0/search/jobs"
NAME = "Get on Board"


def parse(item: dict) -> Job:
    a = item["attributes"]
    company = (((a.get("company") or {}).get("data") or {}).get("attributes") or {}).get("name", "")
    modality = (a.get("remote_modality") or "").lower()
    countries = [c for c in (a.get("countries") or []) if c]
    desc = " ".join(clean_html(a.get(k)) for k in ("description", "functions", "desirable", "projects"))
    published = datetime.fromtimestamp(a["published_at"], tz=timezone.utc) if a.get("published_at") else None
    url = (item.get("links") or {}).get("public_url") or f"https://www.getonbrd.com/jobs/{item['id']}"
    return Job(
        source=NAME,
        id=str(item["id"]),
        title=a.get("title", "").strip(),
        company=company,
        url=url,
        description=desc,
        published=published,
        remote=bool(a.get("remote")) or modality in {"fully_remote", "remote_local", "temporarily_remote"},
        hybrid=modality == "hybrid",
        # "Remote" en countries significa sin restricción; remote_local restringe al país indicado.
        locations=[] if countries in ([], ["Remote"]) else countries,
        salary_min_usd=a.get("min_salary"),
        salary_max_usd=a.get("max_salary"),
        salary_text=(f"USD {a.get('min_salary')}–{a.get('max_salary')}/mes" if a.get("min_salary") else ""),
    )


def fetch(queries: list[str], per_query: int = 30) -> list[Job]:
    jobs: dict[str, Job] = {}
    for q in queries:
        r = get(API, {"query": q, "per_page": per_query, "expand": '["company"]'})
        for item in r.json().get("data", []):
            job = parse(item)
            jobs[job.id] = job
    return list(jobs.values())
