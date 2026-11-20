"""Puntuación con Gemini: compara cada oferta con el perfil y explica el encaje en español."""
from __future__ import annotations

import logging
import os
import time

from pydantic import BaseModel, Field

from .models import Job

log = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"
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
    model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    scored = 0
    for start in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[start:start + BATCH_SIZE]
        prompt = (
            f"{INSTRUCTIONS}\n\nPERFIL DEL CANDIDATO:\n{profile}\n\nOFERTAS:\n\n"
            + "\n\n".join(_describe(i, j) for i, j in enumerate(batch))
        )
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Batch,
                    temperature=0.2,
                ),
            )
            result: Batch = resp.parsed if isinstance(resp.parsed, Batch) else Batch.model_validate_json(resp.text)
        except Exception as exc:
            log.warning("Gemini falló en el lote %d: %s", start // BATCH_SIZE, exc)
            continue
        for a in result.items:
            if 0 <= a.index < len(batch):
                job = batch[a.index]
                job.ai_score, job.ai_reason, job.ai_gaps, job.ai_english = a.score, a.reason, a.gaps, a.english
                scored += 1
        if start + BATCH_SIZE < len(jobs):
            time.sleep(PAUSE_SECONDS)
    return scored
