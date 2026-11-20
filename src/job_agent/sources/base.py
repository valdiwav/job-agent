from __future__ import annotations

import logging
import time

import requests

log = logging.getLogger(__name__)

USER_AGENT = "job-agent/0.1 (personal job search)"
_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json, application/xml, */*"})


def get(url: str, params: dict | None = None, *, timeout: int = 30, retries: int = 2) -> requests.Response:
    """GET con reintentos simples ante errores de red o 429/5xx."""
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = _session.get(url, params=params, timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:  # noqa: PERF203
            last_exc = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    assert last_exc is not None
    raise last_exc
