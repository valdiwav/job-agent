from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import datetime

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def clean_html(text: str | None) -> str:
    if not text:
        return ""
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", text))).strip()


@dataclass
class Job:
    source: str            # nombre de la fuente, p. ej. "Get on Board"
    id: str                # id único dentro de la fuente
    title: str
    company: str
    url: str
    description: str = ""  # texto plano
    published: datetime | None = None
    remote: bool = True
    hybrid: bool = False
    locations: list[str] = field(default_factory=list)  # restricciones de país/región; vacío = sin restricción
    salary_min_usd: float | None = None  # mensual
    salary_max_usd: float | None = None  # mensual
    salary_text: str = ""
    # Rellenados por el pipeline
    keyword_score: int = 0
    ai_score: int | None = None
    ai_reason: str = ""
    ai_gaps: str = ""
    ai_english: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.id}"

    @property
    def final_score(self) -> int:
        return self.ai_score if self.ai_score is not None else self.keyword_score
