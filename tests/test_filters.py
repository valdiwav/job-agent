from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from job_agent import filters
from job_agent.models import Job

CRITERIA = yaml.safe_load((Path(__file__).parents[1] / "config" / "criteria.yaml").read_text(encoding="utf-8"))


def job(**kw) -> Job:
    base = dict(source="T", id="1", title="AI Automation Engineer", company="Acme", url="https://x",
                description="Build LLM agents and automation with Python.")
    base.update(kw)
    return Job(**base)


def run(*jobs, min_clp=1_700_000, seen=()):
    return filters.apply_all(list(jobs), CRITERIA, min_clp, set(seen))


def test_relevant_remote_job_passes():
    assert len(run(job())) == 1


def test_short_keywords_need_whole_word():
    assert filters.count_hits("Chair maker", ["ai"]) == 0
    assert filters.count_hits("Senior AI engineer", ["ai"]) == 1
    assert filters.count_hits("Build AI agents", ["agent"]) == 1


def test_excluded_titles_are_dropped():
    for title in ["Senior AI Engineer", "Lead Automation Engineer", "QA Test Automation Engineer", "Sales AI Specialist"]:
        assert run(job(title=title)) == [], title


def test_irrelevant_job_dropped():
    assert run(job(title="Graphic Designer", description="Figma and branding")) == []


def test_location_restrictions():
    assert run(job(locations=["United States"])) == []
    assert len(run(job(locations=["USA", "Chile"]))) == 1
    assert len(run(job(locations=["LATAM"]))) == 1
    assert len(run(job(locations=["Remote"]))) == 1
    assert run(job(locations=["Remote - US"])) == []


def test_hybrid_only_in_santiago():
    santiago = job(remote=False, hybrid=True, locations=["Chile"], url="https://getonbrd.com/jobs/ai-engineer-santiago")
    (kept,) = run(santiago)
    assert "híbrido" in kept.flags
    lima = job(remote=False, hybrid=True, locations=["Peru"], url="https://x/lima")
    assert run(lima) == []
    onsite = job(remote=False, hybrid=False)
    assert run(onsite) == []


def test_salary_floor_only_when_published():
    assert run(job(salary_min_usd=1000, salary_max_usd=1500)) == []   # 1.425.000 CLP < 1.700.000
    assert len(run(job(salary_min_usd=1800, salary_max_usd=2500))) == 1
    assert len(run(job())) == 1  # sin sueldo publicado: se mantiene


def test_old_jobs_dropped():
    old = datetime.now(timezone.utc) - timedelta(days=30)
    assert run(job(published=old)) == []


def test_seen_and_duplicates():
    a = job(id="1", source="A")
    b = job(id="2", source="B", title="AI  automation engineer", company="ACME")
    assert len(run(a, b)) == 1
    assert run(a, seen={"A:1"}) == []
