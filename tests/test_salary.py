import pytest

from job_agent.salary import parse_salary_text


@pytest.mark.parametrize("text,lo,hi", [
    ("$90k - $120k", 7500, 10000),
    ("$60,000 - $80,000 per year", 5000, 6666.67),
    ("$14/hour", 2240, 2240),
    ("USD 2000 - 3000 / month", 2000, 3000),
])
def test_parse(text, lo, hi):
    a, b = parse_salary_text(text)
    assert a == pytest.approx(lo, rel=0.01)
    assert b == pytest.approx(hi, rel=0.01)


@pytest.mark.parametrize("text", ["", None, "Competitive", "€50k - €60k"])
def test_unparseable(text):
    assert parse_salary_text(text) == (None, None)
