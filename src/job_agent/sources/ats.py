"""Bolsas de empleo públicas de empresas concretas en Greenhouse y Lever."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..models import Job, clean_html
from .base import get

log = logging.getLogger(__name__)


def fetch_greenhouse(slug: str) -> list[Job]:
    data = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", {"content": "true"}).json()
    jobs = []
    for j in data.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        updated = j.get("updated_at")
        jobs.append(Job(
            source=f"Greenhouse · {slug}",
            id=str(j["id"]),
            title=j.get("title", "").strip(),
            company=slug,
            url=j.get("absolute_url", ""),
            description=clean_html(j.get("content")),
            published=datetime.fromisoformat(updated) if updated else None,
            remote="remote" in loc.lower(),
            locations=[loc] if loc else [],
        ))
    return jobs


def fetch_lever(slug: str) -> list[Job]:
    data = get(f"https://api.lever.co/v0/postings/{slug}", {"mode": "json"}).json()
    jobs = []
    for j in data:
        cats = j.get("categories") or {}
        loc = cats.get("location", "") or ""
        workplace = (j.get("workplaceType") or "").lower()
        created = j.get("createdAt")
        jobs.append(Job(
            source=f"Lever · {slug}",
            id=j["id"],
            title=j.get("text", "").strip(),
            company=slug,
            url=j.get("hostedUrl", ""),
            description=clean_html(j.get("descriptionPlain") or j.get("description")),
            published=datetime.fromtimestamp(created / 1000, tz=timezone.utc) if created else None,
            remote=workplace == "remote" or "remote" in loc.lower(),
            hybrid=workplace == "hybrid",
            locations=[loc] if loc else [],
        ))
    return jobs


def fetch(greenhouse: list[str], lever: list[str]) -> list[Job]:
    jobs: list[Job] = []
    for slug in greenhouse:
        try:
            jobs += fetch_greenhouse(slug)
        except Exception as exc:  # una empresa caída no debe parar el resto
            log.warning("Greenhouse %s: %s", slug, exc)
    for slug in lever:
        try:
            jobs += fetch_lever(slug)
        except Exception as exc:
            log.warning("Lever %s: %s", slug, exc)
    return jobs
