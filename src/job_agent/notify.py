"""Resumen diario por correo (SMTP, por defecto Gmail con contraseña de aplicación)."""
from __future__ import annotations

import html
import os
import smtplib
from datetime import date
from email.message import EmailMessage

from .models import Job


def _badge(score: int) -> str:
    color = "#15803d" if score >= 80 else "#ca8a04" if score >= 60 else "#64748b"
    return (f'<span style="background:{color};color:#fff;border-radius:6px;padding:2px 8px;'
            f'font-weight:600">{score}</span>')


def _locations(locs: list[str]) -> str:
    if len(locs) <= 4:
        return ", ".join(locs)
    has_chile = any("chile" in l.lower() for l in locs)
    return f"{len(locs)} países{', incluye Chile' if has_chile else ''}"


def render_html(jobs: list[Job], status: dict[str, str], total: int, used_ai: bool) -> str:
    e = html.escape
    rows = []
    for j in jobs:
        extra = []
        if j.salary_text:
            extra.append(f"💰 {e(j.salary_text)}")
        if j.locations:
            extra.append(f"📍 {e(_locations(j.locations))}")
        if "híbrido" in j.flags:
            extra.append("🏢 híbrido")
        if j.ai_english:
            extra.append(f"🗣️ inglés: {e(j.ai_english)}")
        reason = f'<div style="margin-top:4px">✅ {e(j.ai_reason)}</div>' if j.ai_reason else ""
        gaps = f'<div style="color:#b45309">⚠️ {e(j.ai_gaps)}</div>' if j.ai_gaps else ""
        rows.append(f"""
<tr><td style="padding:12px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top">{_badge(j.final_score)}</td>
<td style="padding:12px 8px;border-bottom:1px solid #e2e8f0">
  <a href="{e(j.url)}" style="font-weight:600;color:#1d4ed8;text-decoration:none">{e(j.title)}</a>
  <div style="color:#334155">{e(j.company)} · vía {e(j.source)}</div>
  <div style="color:#64748b;font-size:13px">{' · '.join(extra)}</div>{reason}{gaps}
</td></tr>""")
    sources = " · ".join(f"{e(k)}: {e(v)}" for k, v in status.items())
    mode = "puntuadas con Gemini" if used_ai else "puntuadas por palabras clave (sin IA)"
    body = "".join(rows) or '<tr><td style="padding:12px">Hoy no hay ofertas nuevas que pasen los filtros.</td></tr>'
    return f"""<!doctype html><html><head><meta charset="utf-8"></head><body style="font-family:Segoe UI,Arial,sans-serif;color:#0f172a;max-width:760px">
<h2 style="margin-bottom:4px">Ofertas del {date.today():%d-%m-%Y}</h2>
<p style="color:#475569;margin-top:0">{len(jobs)} mejores de {total} nuevas que pasaron los filtros, {mode}.</p>
<table style="border-collapse:collapse;width:100%">{body}</table>
<p style="color:#94a3b8;font-size:12px;margin-top:16px">Fuentes: {sources}</p>
</body></html>"""


def send_email(subject: str, html_body: str) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    to = os.getenv("EMAIL_TO", user)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.set_content("Este correo necesita un cliente con HTML.")
    msg.add_alternative(html_body, subtype="html")
    with smtplib.SMTP_SSL(host, port, timeout=30) as s:
        s.login(user, password)
        s.send_message(msg)
