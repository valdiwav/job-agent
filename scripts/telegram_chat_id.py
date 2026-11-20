"""Muestra el chat_id de tu conversación con el bot.

1. Crea el bot con @BotFather en Telegram (/newbot) y pon el token en .env como TELEGRAM_BOT_TOKEN.
2. Abre el chat con tu bot y mándale cualquier mensaje (por ejemplo /start).
3. Ejecuta:  .venv/Scripts/python scripts/telegram_chat_id.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from job_agent.main import ROOT, load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
import os  # noqa: E402

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    sys.exit("Falta TELEGRAM_BOT_TOKEN en .env")

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
if not r.ok:
    sys.exit(f"Telegram respondió {r.status_code}: {r.json().get('description', '')} (¿token correcto?)")

chats = {}
for update in r.json().get("result", []):
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat")
    if chat:
        chats[chat["id"]] = chat.get("first_name") or chat.get("title") or ""

if not chats:
    sys.exit("No hay mensajes todavía: escríbele algo a tu bot en Telegram y vuelve a ejecutar este script.")
for chat_id, name in chats.items():
    print(f"TELEGRAM_CHAT_ID={chat_id}   ({name})")
