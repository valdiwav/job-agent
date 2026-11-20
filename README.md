# job-agent

Agente que busca cada mañana ofertas **remotas de IA aplicada y automatización** en varias bolsas de empleo, descarta las que no encajan, **puntúa las demás con un LLM (Gemini)** según tu perfil y te manda por correo un resumen con las mejores y el motivo de cada puntuación.

Lo hice para dejar de revisar portales a mano. Inspiración: el consejo de usar la IA como palanca en la búsqueda de empleo y postular solo a lo que de verdad mejora tu situación.

```
 Get on Board ─┐
 Remotive ─────┤                 ┌─ antigüedad ≤ 7 días
 Himalayas ────┼─► 500 ofertas ─►├─ título relevante / sin seniority alta ─► ~20 ─► Gemini ─► top 15 ─► Telegram / correo
 Remote OK ────┤                 ├─ remoto (o híbrido en Santiago)            puntúa 0-100,
 We Work ──────┤                 ├─ ubicación compatible con Chile/LATAM      explica encaje
 Remotely      │                 ├─ sueldo publicado ≥ mínimo                 y carencias
 Greenhouse ───┘                 └─ sin duplicados ni ya enviadas
 / Lever
```

## Qué hace

- **6 fuentes** con APIs o feeds públicos: Get on Board (Chile/LATAM), Remotive, Himalayas, Remote OK, We Work Remotely y las bolsas Greenhouse/Lever de las empresas que elijas. No hace scraping de LinkedIn.
- **Filtros deterministas** (`src/job_agent/filters.py`): palabras clave con límites de palabra, exclusión por título (senior, lead, QA, ventas…), restricciones de país, modalidad, sueldo normalizado a USD mensuales y deduplicación entre fuentes.
- **Puntuación con LLM** (`src/job_agent/scorer.py`): Gemini recibe el perfil y lotes de 8 ofertas y devuelve JSON validado con Pydantic (puntuación, por qué encaja, qué falta, nivel de inglés exigido). Si no hay clave o la API falla, se usa la puntuación por palabras clave.
- **Aviso diario por Telegram** (las 8 mejores, con nota y motivo) y/o **correo HTML** con enlace a cada oferta original y la fuente citada, como piden las condiciones de Remotive y Remote OK.
- **Memoria**: no repite ofertas ya enviadas (60 días), guardada con `actions/cache`.
- **Tests** de filtros, sueldos, parseo de fuentes y del puntuador con un cliente simulado.

## Uso en local

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Windows (en Linux/macOS: .venv/bin/pip)
cp .env.example .env                                  # y rellénalo
cp profile.example.md profile.md                      # y escribe tu perfil
PYTHONPATH=src .venv/Scripts/python -m job_agent --dry-run   # imprime el top y genera out/report.html
PYTHONPATH=src .venv/Scripts/python -m pytest -q
```

Opciones: `--dry-run` (no envía correo ni guarda estado) y `--no-ai` (solo palabras clave).

## Uso en GitHub Actions

El workflow `.github/workflows/daily.yml` corre cada día a las 08:00 de Santiago y también a mano desde la pestaña *Actions*.

| Tipo | Nombre | Valor |
|---|---|---|
| Secret | `GEMINI_API_KEY` | Clave gratuita de [Google AI Studio](https://aistudio.google.com/apikey) |
| Secret | `PROFILE_TEXT` | El contenido de tu `profile.md` |
| Secret | `SMTP_USER` | Tu Gmail |
| Secret | `SMTP_PASSWORD` | [Contraseña de aplicación](https://myaccount.google.com/apppasswords) de Gmail (no tu contraseña normal) |
| Secret | `EMAIL_TO` | Dónde recibir el resumen |
| Secret | `TELEGRAM_BOT_TOKEN` | Token del bot creado con [@BotFather](https://t.me/BotFather) (opcional) |
| Secret | `TELEGRAM_CHAT_ID` | Tu chat con el bot; se obtiene con `scripts/telegram_chat_id.py` (opcional) |
| Variable | `MIN_SALARY_CLP` | Sueldo mínimo mensual en CLP (por defecto 1.700.000) |

Para cargarlos desde tu `.env` y `profile.md` sin copiarlos a mano: `powershell -ExecutionPolicy Bypass -File scripts\cargar_secretos.ps1`.

Los criterios (palabras clave, ubicaciones, empresas a vigilar) están en `config/criteria.yaml`.

## Stack

Python 3.12 · requests · Pydantic · google-genai (Gemini) · PyYAML · pytest · GitHub Actions
