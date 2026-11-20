"""Filtros deterministas: antigüedad, título, relevancia, ubicación/modalidad, sueldo y duplicados."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from .models import Job

NO_RESTRICTION = {"remote", "remoto", "anywhere", "worldwide", "global", "anywhere in the world"}


@lru_cache(maxsize=512)
def _pattern(keyword: str) -> re.Pattern[str]:
    kw = re.escape(keyword.strip().lower())
    # Palabras cortas ("ai", "ia", "qa", "sr") exigen palabra completa; las largas admiten sufijos ("agent" → "agents").
    if len(keyword.strip()) <= 3:
        return re.compile(rf"(?<!\w){kw}(?!\w)")
    return re.compile(rf"(?<!\w){kw}")


def count_hits(text: str, keywords: list[str]) -> int:
    t = text.lower()
    return sum(1 for kw in keywords if _pattern(kw).search(t))


def is_recent(job: Job, max_age_days: int, now: datetime | None = None) -> bool:
    if job.published is None:
        return True
    now = now or datetime.now(timezone.utc)
    published = job.published if job.published.tzinfo else job.published.replace(tzinfo=timezone.utc)
    return now - published <= timedelta(days=max_age_days)


def title_excluded(job: Job, exclude: list[str]) -> bool:
    return count_hits(job.title, exclude) > 0


def relevance(job: Job, include: list[str]) -> int:
    """0 si no es relevante; si lo es, una puntuación 1–100 por palabras clave."""
    in_title = count_hits(job.title, include)
    in_desc = count_hits(job.description, include)
    if in_title == 0 and in_desc < 2:
        return 0
    return min(100, 25 * in_title + 5 * in_desc)


def location_ok(job: Job, accepted: list[str], hybrid_cities: list[str]) -> bool:
    locs = [l.strip().lower() for l in job.locations if l and l.strip()]
    unrestricted = not locs or all(l in NO_RESTRICTION for l in locs)
    in_accepted = unrestricted or any(a.lower() in l for l in locs for a in accepted)

    if job.hybrid and not job.remote:
        haystack = " ".join([job.url, job.title, job.description, *locs]).lower()
        if any(c.lower() in haystack for c in hybrid_cities) and (unrestricted or any("chile" in l for l in locs)):
            if "híbrido" not in job.flags:
                job.flags.append("híbrido")
            return True
        return False
    return job.remote and in_accepted


def salary_ok(job: Job, min_clp: int | None, usd_to_clp: float) -> bool:
    """Descarta solo si el sueldo está publicado y su máximo queda por debajo del mínimo."""
    if not min_clp:
        return True
    top = job.salary_max_usd or job.salary_min_usd
    if top is None:
        return True
    return top * usd_to_clp >= min_clp


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def dedupe(jobs: list[Job]) -> list[Job]:
    """Une la misma oferta publicada en varias fuentes; se queda con la de mayor puntuación."""
    best: dict[tuple[str, str], Job] = {}
    for job in jobs:
        k = (_norm(job.title), _norm(job.company))
        if k not in best or job.keyword_score > best[k].keyword_score:
            best[k] = job
    return list(best.values())


def apply_all(jobs: list[Job], criteria: dict, min_clp: int | None, seen: set[str]) -> list[Job]:
    out: list[Job] = []
    for job in jobs:
        if job.key in seen:
            continue
        if not is_recent(job, int(criteria.get("max_age_days", 7))):
            continue
        if title_excluded(job, criteria.get("exclude_title_keywords", [])):
            continue
        score = relevance(job, criteria.get("include_keywords", []))
        if score == 0:
            continue
        if not location_ok(job, criteria.get("accepted_locations", []), criteria.get("hybrid_cities", [])):
            continue
        if not salary_ok(job, min_clp, float(criteria.get("usd_to_clp", 950))):
            continue
        job.keyword_score = score
        out.append(job)
    return sorted(dedupe(out), key=lambda j: j.keyword_score, reverse=True)
