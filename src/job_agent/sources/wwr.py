"""We Work Remotely (weworkremotely.com) vía RSS público."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from ..models import Job, clean_html
from .base import get

FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]
NAME = "We Work Remotely"


def parse(item: ET.Element) -> Job:
    raw_title = (item.findtext("title") or "").strip()
    company, _, title = raw_title.partition(":")
    if not title:
        company, title = "", raw_title
    region = (item.findtext("region") or "").strip()
    pub = item.findtext("pubDate")
    link = (item.findtext("link") or "").strip()
    return Job(
        source=NAME,
        id=(item.findtext("guid") or link).strip(),
        title=title.strip(),
        company=company.strip(),
        url=link,
        description=clean_html(item.findtext("description")),
        published=parsedate_to_datetime(pub) if pub else None,
        locations=[r.strip() for r in region.split(",") if r.strip()],
    )


def fetch(queries: list[str] | None = None) -> list[Job]:
    jobs: dict[str, Job] = {}
    for feed in FEEDS:
        root = ET.fromstring(get(feed).content)
        for item in root.iter("item"):
            job = parse(item)
            jobs[job.id] = job
    return list(jobs.values())
