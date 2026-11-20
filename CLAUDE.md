# job-agent

Agente diario de búsqueda de empleo: descarga ofertas de APIs públicas, filtra, puntúa con Gemini contra el perfil y manda un correo. Hereda las reglas de `../CLAUDE.md`. Uso y arquitectura en `README.md`.

## Estado (2026-11-20)
- Fase: MVP implementado y probado en local en modo `--dry-run --no-ai` (505 ofertas descargadas, 21 pasan filtros). 24 tests en verde.
- Pendiente del usuario: crear la clave de Gemini y la contraseña de aplicación de Gmail, crear el repo en GitHub y cargar los secretos.
- Sin probar todavía: la puntuación real con Gemini, el envío por correo y el workflow en GitHub Actions.
- Siguiente paso: primera ejecución real con `GEMINI_API_KEY` en `.env` y ajustar `config/criteria.yaml` según los resultados.

## Comandos
- Tests: `.venv/Scripts/python -m pytest -q`
- Prueba sin enviar: `PYTHONPATH=src .venv/Scripts/python -m job_agent --dry-run` (añadir `--no-ai` para no gastar cuota)

## Convenciones
- Cada fuente en `src/job_agent/sources/<fuente>.py` con `parse()` puro (testeable) y `fetch()`; se registra en `sources/__init__.py`.
- Sueldos siempre en USD mensuales (`salary.py`); el mínimo en CLP viene de `MIN_SALARY_CLP`.
- Datos personales nunca en el repo: `profile.md` y `.env` están en `.gitignore`; en Actions van como secretos.
- Respetar las condiciones de cada API: enlazar la oferta original, citar la fuente, Remotive una sola llamada por ejecución. Nada de scraping de LinkedIn.
