"""El puntuador con un cliente de Gemini simulado (sin red ni clave real)."""
import sys
import types

from job_agent import scorer
from job_agent.models import Job


def _fake_genai(monkeypatch, response_items, calls):
    class Models:
        def generate_content(self, model, contents, config):
            calls.append(contents)
            return types.SimpleNamespace(parsed=scorer.Batch(items=response_items), text="")

    class Client:
        def __init__(self, api_key):
            self.models = Models()

    genai = types.ModuleType("google.genai")
    genai.Client = Client
    gtypes = types.ModuleType("google.genai.types")
    gtypes.GenerateContentConfig = lambda **kw: kw
    genai.types = gtypes
    google = types.ModuleType("google")
    google.genai = genai
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", gtypes)
    monkeypatch.setattr(scorer, "PAUSE_SECONDS", 0)


def test_scores_are_applied(monkeypatch):
    calls = []
    items = [scorer.Assessment(index=0, score=88, reason="Encaja", gaps="Pide inglés", english="fluido"),
             scorer.Assessment(index=5, score=99, reason="índice fuera de rango", gaps="", english="no")]
    _fake_genai(monkeypatch, items, calls)
    jobs = [Job(source="T", id="1", title="AI Eng", company="C", url="u", keyword_score=40)]
    assert scorer.score_jobs(jobs, "perfil", api_key="k") == 1
    assert (jobs[0].ai_score, jobs[0].final_score, jobs[0].ai_english) == (88, 88, "fluido")
    assert "perfil" in calls[0] and "AI Eng" in calls[0]


def test_falls_back_when_model_busy_or_retired(monkeypatch):
    class ApiError(Exception):
        def __init__(self, code):
            self.code = code

    tried = []

    class Client:
        def generate_content(self, model, contents, config):
            tried.append(model)
            if model == "a":
                raise ApiError(503)
            if model == "b":
                raise ApiError(404)
            return types.SimpleNamespace(parsed=scorer.Batch(items=[]), text="")

    monkeypatch.setattr(scorer, "RETRY_WAITS", [0])
    _, used = scorer._generate(types.SimpleNamespace(models=Client()), ["a", "b", "c"], "p", {})
    assert used == "c"
    assert tried == ["a", "a", "b", "c"]  # reintenta el saturado una vez; el retirado no


def test_without_key_keeps_keyword_score(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    jobs = [Job(source="T", id="1", title="AI Eng", company="C", url="u", keyword_score=40)]
    assert scorer.score_jobs(jobs, "perfil") == 0
    assert jobs[0].final_score == 40
