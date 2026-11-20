"""Punto de entrada: python -m job_agent [--dry-run] [--no-ai]"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

import yaml

from . import filters, notify, scorer, sources, state, telegram

ROOT = Path(__file__).resolve().parents[2]
log = logging.getLogger("job_agent")


def load_dotenv(path: Path) -> None:
    """Carga un .env sencillo (CLAVE=valor) sin pisar variables ya definidas."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_profile() -> str:
    if os.getenv("PROFILE_TEXT"):
        return os.environ["PROFILE_TEXT"]
    for name in ("profile.md", "profile.example.md"):
        p = ROOT / name
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


def run(dry_run: bool, use_ai: bool) -> int:
    criteria = yaml.safe_load((ROOT / "config" / "criteria.yaml").read_text(encoding="utf-8"))
    min_clp = int(os.getenv("MIN_SALARY_CLP", "0")) or None
    state_path = Path(os.getenv("STATE_PATH", ROOT / "data" / "seen.json"))
    seen = state.load(state_path)

    jobs, status = sources.fetch_all(criteria)
    log.info("Descargadas %d ofertas: %s", len(jobs), status)

    candidates = filters.apply_all(jobs, criteria, min_clp, set(seen))
    log.info("%d ofertas nuevas pasan los filtros", len(candidates))

    to_score = candidates[: int(criteria.get("max_to_score", 40))]
    scored = scorer.score_jobs(to_score, load_profile()) if use_ai else 0
    log.info("%d ofertas puntuadas con IA", scored)

    ranked = sorted(to_score, key=lambda j: j.final_score, reverse=True)
    top = ranked[: int(criteria.get("max_in_email", 15))]
    body = notify.render_html(top, status, len(candidates), used_ai=scored > 0)

    out = ROOT / "out" / "report.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(body, encoding="utf-8")
    log.info("Informe guardado en %s", out)

    if dry_run:
        for j in top:
            print(f"{j.final_score:>3}  {j.title} — {j.company} [{j.source}]\n     {j.url}")
        return 0

    best = top[0].final_score if top else 0
    channels = {}
    if os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"):
        channels["correo"] = lambda: notify.send_email(
            f"🔎 {len(top)} ofertas IA/automatización · mejor {best}/100 · {date.today():%d-%m}", body)
    if telegram.is_configured():
        channels["Telegram"] = lambda: telegram.send(
            telegram.render(top, len(candidates), int(criteria.get("max_in_telegram", 8))))
    if not channels:
        log.error("No hay canal configurado: define SMTP_* o TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID")
        return 1

    sent = []
    for name, send in channels.items():
        try:
            send()
            sent.append(name)
            log.info("Enviado por %s", name)
        except Exception as exc:  # un canal caído no debe impedir el otro
            log.error("Falló el envío por %s: %s", name, exc)
    if not sent:
        return 1
    # Se marcan todas las puntuadas para no gastar IA en ellas mañana.
    state.save(state_path, seen, [j.key for j in to_score])
    return 0 if len(sent) == len(channels) else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Busca ofertas remotas de IA y automatización y te las manda por correo.")
    parser.add_argument("--dry-run", action="store_true", help="No envía correo ni guarda estado; imprime el top y genera out/report.html")
    parser.add_argument("--no-ai", action="store_true", help="Puntúa solo por palabras clave")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv(ROOT / ".env")
    sys.exit(run(args.dry_run, not args.no_ai))


if __name__ == "__main__":
    main()
