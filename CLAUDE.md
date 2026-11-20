# job-agent

Agente diario de búsqueda de empleo: descarga ofertas de APIs públicas, filtra, puntúa con Gemini contra el perfil y manda un correo. Hereda las reglas de `../CLAUDE.md`. Uso y arquitectura en `README.md`.

## Estado (2026-11-20)
- Fase: MVP funcionando en local: Gemini puntúa (con reintentos y modelos de respaldo) y el correo llega (primer envío real 2026-11-20). 25 tests en verde.
- Pendiente: crear el repo público en GitHub (con permiso del usuario) y cargar los secretos.
- Sin probar todavía: el workflow en GitHub Actions.
- Siguiente paso: revisar con el usuario el primer correo y ajustar `config/criteria.yaml`; luego publicar en GitHub.

## Comandos
- Tests: `.venv/Scripts/python -m pytest -q`
- Prueba sin enviar: `PYTHONPATH=src .venv/Scripts/python -m job_agent --dry-run` (añadir `--no-ai` para no gastar cuota)

## Convenciones
- Cada fuente en `src/job_agent/sources/<fuente>.py` con `parse()` puro (testeable) y `fetch()`; se registra en `sources/__init__.py`.
- Sueldos siempre en USD mensuales (`salary.py`); el mínimo en CLP viene de `MIN_SALARY_CLP`.
- Datos personales nunca en el repo: `profile.md` y `.env` están en `.gitignore`; en Actions van como secretos.
- Respetar las condiciones de cada API: enlazar la oferta original, citar la fuente, Remotive una sola llamada por ejecución. Nada de scraping de LinkedIn.
