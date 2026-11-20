from job_agent import telegram
from job_agent.models import Job


def job(i: int, **kw) -> Job:
    base = dict(source="Himalayas", id=str(i), title=f"AI Engineer <{i}> & co", company="Acme", url="https://x/?a=1&b=2",
                ai_score=80, ai_reason="Encaja por automatización", ai_english="lectura")
    base.update(kw)
    return Job(**base)


def test_render_escapes_html_and_respects_limit():
    (msg,) = telegram.render([job(i) for i in range(20)], total=20, limit=8)
    assert msg.count("🟢") == 8
    assert "&lt;0&gt; &amp; co" in msg            # el título no rompe el HTML
    assert 'href="https://x/?a=1&amp;b=2"' in msg  # ni el enlace
    assert "<i>Encaja por automatización</i>" in msg


def test_long_output_is_split():
    long = [job(i, ai_reason="x" * 900) for i in range(8)]
    msgs = telegram.render(long, total=8)
    assert len(msgs) > 1
    assert all(len(m) <= telegram.MAX_LEN for m in msgs)


def test_empty_day():
    (msg,) = telegram.render([], total=0)
    assert "no hay ofertas nuevas" in msg
