"""Puntuación con Gemini: compara cada oferta con el perfil y explica el encaje en español."""
from __future__ import annotations

import logging
import os
import time

from pydantic import BaseModel, Field

from .models import Job

log = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.5-flash"  # el más fiable en el nivel gratuito (nov. 2026); se cambia con GEMINI_MODEL
# Si el modelo principal está saturado (503/429) o retirado (404), se prueban estos en orden.
FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.1-flash-lite"]
RETRY_WAITS = [10, 30]  # segundos entre reintentos con el mismo modelo
BATCH_SIZE = 8
PAUSE_SECONDS = 7  # margen para el límite de peticiones por minuto del nivel gratuito
DESC_CHARS = 2500


class Assessment(BaseModel):
    index: int = Field(description="Índice de la oferta en la lista recibida")
    score: int = Field(ge=0, le=100, description="Encaje 0-100 con el perfil y los criterios")
    reason: str = Field(description="Por qué encaja, 1-2 frases en español, concreto")
    gaps: str = Field(description="Qué le falta al candidato o riesgos (inglés, seniority, stack), 1 frase en español")
    english: str = Field(description="Nivel de inglés que exige: 'no', 'lectura', 'conversacional' o 'fluido'")


class Batch(BaseModel):
    items: list[Assessment]


INSTRUCTIONS = """Eres un reclutador técnico que filtra ofertas para un candidato concreto.
Puntúa cada oferta de 0 a 100 según lo bien que encaja con el PERFIL y los CRITERIOS.

Criterios del candidato:
- Prioridad: roles de IA aplicada, automatización de procesos, agentes LLM, Forward Deployed / Solutions / Implementation Engineer.
- Nivel: junior o semi-senior (menos de 2 años en el rol actual). Penaliza fuerte lo que pida 5+ años o liderazgo.
- Modalidad: 100% remoto ideal. Las marcadas "híbrido" solo valen si el sueldo es claramente alto: penalízalas 20 puntos.
- Idioma: prefiere español. Inglés técnico bueno pero conversación no fluida: penaliza las que exigen inglés fluido/nativo.
- Sueldo: busca una mejora clara; si la oferta da un rango, tenlo en cuenta.

Escala: 80-100 postular ya · 60-79 vale la pena revisar · 40-59 encaje parcial · <40 no encaja.
Sé estricto y honesto; no infles puntuaciones. Responde para TODAS las ofertas, usando su índice."""


def _describe(i: int, job: Job) -> str:
    parts = [
        f"[{i}] {job.title} — {job.company} ({job.source})",
        f"Ubicación/restricciones: {', '.join(job.locations) or 'sin restricción'}",
        f"Modalidad: {'híbrido' if 'híbrido' in job.flags else 'remoto'}",
        f"Sueldo: {job.salary_text or 'no indicado'}",
        f"Descripción: {job.description[:DESC_CHARS]}",
    ]
    return "\n".join(parts)


def _status(exc: Exception) -> int | None:
    code = getattr(exc, "code", None)
    return code if isinstance(code, int) else None


def _generate(client, models: list[str], prompt: str, config) -> tuple[Batch, str]:
    """Llama a Gemini con reintentos y modelos de respaldo. Devuelve (resultado, modelo usado)."""
    last: Exception | None = None
    for model in models:
        for attempt in range(len(RETRY_WAITS) + 1):
            try:
                resp = client.models.generate_content(model=model, contents=prompt, config=config)
                parsed = resp.parsed if isinstance(resp.parsed, Batch) else Batch.model_validate_json(resp.text)
                return parsed, model
            except Exception as exc:
                last = exc
                status = _status(exc)
                if status == 404:
                    break  # modelo retirado: pasar al siguiente
                if status in (429, 500, 503) and attempt < len(RETRY_WAITS):
                    time.sleep(RETRY_WAITS[attempt])
                    continue
                if status in (429, 500, 503):
                    break  # sigue saturado: probar otro modelo
                raise  # error de clave, petición, etc.: no tiene sentido insistir
        log.info("Modelo %s no disponible (%s), probando el siguiente", model, _status(last) if last else "?")
    assert last is not None
    raise last


def score_jobs(jobs: list[Job], profile: str, api_key: str | None = None, model: str | None = None) -> int:
    """Rellena ai_score/ai_reason/… en cada Job. Devuelve cuántas ofertas se puntuaron.

    Si no hay clave o la API falla, las ofertas conservan su puntuación por palabras clave.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or not jobs:
        return 0
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    primary = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    models = [primary, *[m for m in FALLBACK_MODELS if m != primary]]
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Batch,
        temperature=0.2,
    )
    scored = 0
    for start in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[start:start + BATCH_SIZE]
        prompt = (
            f"{INSTRUCTIONS}\n\nPERFIL DEL CANDIDATO:\n{profile}\n\nOFERTAS:\n\n"
            + "\n\n".join(_describe(i, j) for i, j in enumerate(batch))
        )
        try:
            result, used = _generate(client, models, prompt, config)
        except Exception as exc:
            log.warning("Gemini falló en el lote %d: %s", start // BATCH_SIZE, exc)
            continue
        if used != models[0]:
            # Si el principal falló, los lotes siguientes empiezan por el que sí respondió.
            models = [used, *[m for m in models if m != used]]
        log.info("Lote %d puntuado con %s", start // BATCH_SIZE, used)
        for a in result.items:
            if 0 <= a.index < len(batch):
                job = batch[a.index]
                job.ai_score, job.ai_reason, job.ai_gaps, job.ai_english = a.score, a.reason, a.gaps, a.english
                scored += 1
        if start + BATCH_SIZE < len(jobs):
            time.sleep(PAUSE_SECONDS)
    return scored
