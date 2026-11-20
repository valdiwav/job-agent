"""Aviso corto por Telegram (Bot API oficial y gratuita)."""
from __future__ import annotations

import html
import os
from datetime import date

import requests

from .models import Job

API = "https://api.telegram.org/bot{token}/{method}"
MAX_LEN = 4000  # Telegram admite 4096 caracteres por mensaje; dejamos margen


def is_configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def _icon(score: int) -> str:
    return "🟢" if score >= 80 else "🟡" if score >= 60 else "⚪"


def render(jobs: list[Job], total: int, limit: int = 8) -> list[str]:
    """Devuelve uno o más mensajes en HTML de Telegram, cada uno bajo el límite de longitud."""
    e = html.escape
    header = f"<b>🔎 Ofertas del {date.today():%d-%m}</b>\n{min(len(jobs), limit)} mejores de {total} nuevas\n"
    if not jobs:
        return [header + "\nHoy no hay ofertas nuevas que pasen los filtros."]
    blocks = []
    for j in jobs[:limit]:
        lines = [f'{_icon(j.final_score)} <b>{j.final_score}</b> · <a href="{e(j.url, quote=True)}">{e(j.title)}</a>',
                 f"{e(j.company)} · {e(j.source)}"]
        details = [d for d in (j.salary_text and f"💰 {j.salary_text}",
                               "🏢 híbrido" if "híbrido" in j.flags else "",
                               j.ai_english and f"🗣️ inglés: {j.ai_english}") if d]
        if details:
            lines.append(e(" · ".join(details)))
        if j.ai_reason:
            lines.append(f"<i>{e(j.ai_reason)}</i>")
        blocks.append("\n".join(lines))

    messages, current = [], header
    for block in blocks:
        if len(current) + len(block) + 2 > MAX_LEN:
            messages.append(current)
            current = ""
        current += "\n" + block + "\n"
    messages.append(current)
    return messages


def send(messages: list[str]) -> None:
    token, chat_id = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    for text in messages:
        r = requests.post(API.format(token=token, method="sendMessage"), timeout=30, json={
            "chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True,
        })
        if not r.ok:
            # No se incluye la URL en el error: contiene el token del bot.
            raise RuntimeError(f"Telegram respondió {r.status_code}: {r.json().get('description', '')}")
