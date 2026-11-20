# job-agent

Agente diario de búsqueda de empleo: descarga ofertas de APIs públicas, filtra, puntúa con Gemini contra el perfil y manda un correo. Hereda las reglas de `../CLAUDE.md`. Uso y arquitectura en `README.md`.

## Estado (2026-11-20)
- Fase: MVP funcionando en local y publicado en github.com/valdiwav/job-agent. Gemini 3.5 Flash puntúa; correo y Telegram (@ValdiLinked_bot) probados con envío real el 2026-11-20. 28 tests en verde.
- En producción: GitHub Actions corre cada día a las 08:00 de Santiago (secretos cargados; prueba en modo dry-run OK el 2026-11-20).
- Ojo: GitHub desactiva los cron de repos públicos tras 60 días sin commits; reactivar desde la pestaña Actions si deja de llegar.
- Siguiente paso: tras unos días de avisos, ajustar `config/criteria.yaml` (palabras clave, exclusiones, nota mínima) según lo que llegue.

## Comandos
- Tests: `.venv/Scripts/python -m pytest -q`
- Prueba sin enviar: `PYTHONPATH=src .venv/Scripts/python -m job_agent --dry-run` (añadir `--no-ai` para no gastar cuota)

## Convenciones
- Cada fuente en `src/job_agent/sources/<fuente>.py` con `parse()` puro (testeable) y `fetch()`; se registra en `sources/__init__.py`.
- Sueldos siempre en USD mensuales (`salary.py`); el mínimo en CLP viene de `MIN_SALARY_CLP`.
- Datos personales nunca en el repo: `profile.md` y `.env` están en `.gitignore`; en Actions van como secretos.
- Respetar las condiciones de cada API: enlazar la oferta original, citar la fuente, Remotive una sola llamada por ejecución. Nada de scraping de LinkedIn.
