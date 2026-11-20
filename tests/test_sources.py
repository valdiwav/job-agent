"""Parseo de cada fuente con ejemplos reducidos de sus respuestas reales."""
from job_agent.sources import getonbrd, himalayas, remoteok, remotive


def test_getonbrd_remote_local_chile():
    item = {"id": "ai-eng", "links": {"public_url": "https://www.getonbrd.com/jobs/ai-eng"},
            "attributes": {"title": "AI Engineer", "remote": True, "remote_modality": "remote_local",
                           "countries": ["Chile"], "min_salary": 2000, "max_salary": 2800, "published_at": 1795000000,
                           "description": "<p>LLM</p>", "company": {"data": {"attributes": {"name": "Acme"}}}}}
    j = getonbrd.parse(item)
    assert (j.company, j.remote, j.hybrid, j.locations, j.salary_max_usd) == ("Acme", True, False, ["Chile"], 2800)


def test_getonbrd_hybrid_and_unrestricted():
    base = {"id": "x", "links": {}, "attributes": {"title": "T", "published_at": None}}
    hybrid = getonbrd.parse({**base, "attributes": {**base["attributes"], "remote": False,
                                                    "remote_modality": "hybrid", "countries": ["Chile"]}})
    assert hybrid.hybrid and not hybrid.remote
    anywhere = getonbrd.parse({**base, "attributes": {**base["attributes"], "remote": True,
                                                      "remote_modality": "fully_remote", "countries": ["Remote"]}})
    assert anywhere.locations == []


def test_remotive_salary_and_location():
    j = remotive.parse({"id": 1, "title": "AI Eng", "company_name": "C", "url": "u",
                        "candidate_required_location": "LATAM, USA", "salary": "$60k - $72k",
                        "publication_date": "2026-11-19T14:58:42", "description": ""})
    assert j.locations == ["LATAM", "USA"]
    assert j.salary_min_usd == 5000


def test_remoteok_annual_salary():
    j = remoteok.parse({"id": "9", "position": "Automation Engineer", "company": "C", "epoch": 1795000000,
                        "salary_min": 60000, "salary_max": 90000, "tags": ["python"], "location": ""})
    assert (j.salary_min_usd, j.salary_max_usd, j.locations) == (5000, 7500, [])


def test_himalayas_non_usd_salary_ignored():
    j = himalayas.parse({"title": "AI", "guid": "g", "minSalary": "1800", "maxSalary": "2150",
                         "salaryPeriod": "monthly", "currency": "EUR", "locationRestrictions": ["Chile"],
                         "pubDate": "1795000000"})
    assert j.salary_min_usd is None and j.locations == ["Chile"]
