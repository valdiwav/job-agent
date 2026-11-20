"""Normalización de sueldos a USD mensuales."""
from __future__ import annotations

import re

_NUM = re.compile(r"(\d[\d.,]*)\s*([kK])?")


def to_monthly(amount: float, period: str | None) -> float:
    p = (period or "").lower()
    if p.startswith(("year", "annual", "anual")):
        return amount / 12
    if p.startswith(("hour", "hora")):
        return amount * 160
    if p.startswith(("week", "seman")):
        return amount * 4.33
    if p.startswith(("month", "mensual", "mes")):
        return amount
    # Sin periodo: un número grande casi siempre es anual.
    return amount / 12 if amount > 20000 else amount


def _parse_number(raw: str, k: str | None) -> float | None:
    s = raw.rstrip(".,")
    # "120,000" / "120.000" -> miles; "1.5" -> decimal
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    else:
        s = s.replace(",", ".")
    try:
        value = float(s)
    except ValueError:
        return None
    return value * 1000 if k else value


def parse_salary_text(text: str | None) -> tuple[float | None, float | None]:
    """Extrae (mín, máx) en USD mensuales de un texto libre como '$90k - $120k/year' o '$14/hour'.

    Solo se interpretan textos en USD o sin moneda; otros devuelven (None, None).
    """
    if not text:
        return None, None
    t = text.lower()
    if any(c in t for c in ("€", "eur", "£", "gbp", "inr", "₹")):
        return None, None
    nums = [n for n in (_parse_number(m.group(1), m.group(2)) for m in _NUM.finditer(t)) if n]
    nums = [n for n in nums if n >= 5]  # descarta ruido como "2 años"
    if not nums:
        return None, None
    period = None
    if re.search(r"/\s*h|hour|hora|hr\b", t):
        period = "hour"
    elif re.search(r"year|annual|/\s*y|año|anual|yr\b", t):
        period = "year"
    elif re.search(r"month|/\s*mo|mes|mensual", t):
        period = "month"
    lo, hi = min(nums[:2]), max(nums[:2])
    return to_monthly(lo, period), to_monthly(hi, period)
