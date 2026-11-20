"""Fuentes de ofertas. Cada una devuelve una lista de `Job`; un fallo en una no detiene las demás."""
from __future__ import annotations

import logging
from collections.abc import Callable

from ..models import Job
from . import ats, getonbrd, himalayas, remoteok, remotive, wwr

log = logging.getLogger(__name__)


def fetch_all(criteria: dict) -> tuple[list[Job], dict[str, str]]:
    """Devuelve (ofertas, estado por fuente). El estado es 'N ofertas' o el error."""
    queries = criteria.get("search_queries", [])
    tasks: dict[str, Callable[[], list[Job]]] = {
        getonbrd.NAME: lambda: getonbrd.fetch(queries),
        remotive.NAME: remotive.fetch,
        himalayas.NAME: lambda: himalayas.fetch(queries),
        remoteok.NAME: remoteok.fetch,
        wwr.NAME: wwr.fetch,
    }
    gh, lv = criteria.get("greenhouse_companies") or [], criteria.get("lever_companies") or []
    if gh or lv:
        tasks["Greenhouse/Lever"] = lambda: ats.fetch(gh, lv)

    jobs: list[Job] = []
    status: dict[str, str] = {}
    for name, task in tasks.items():
        try:
            found = task()
            jobs += found
            status[name] = f"{len(found)} ofertas"
        except Exception as exc:
            log.warning("Fuente %s falló: %s", name, exc)
            status[name] = f"error: {exc.__class__.__name__}"
    return jobs, status
