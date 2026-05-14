import json

import httpx

from app.models import LearningPlan, Mastery
from app.services.plan import generate_plan
from tests.conftest import FakeLLM


def _seed_mastery(session, user, topics, values):
    for topic, v in zip(topics, values):
        a, b = v * 10, (1 - v) * 10
        session.add(Mastery(user_id=user.id, topic_id=topic.id, alpha=a, beta=b))
    session.flush()


async def test_generate_plan_uses_llm_response(session, seeded, user):
    tid = seeded["topics"][0].id
    days = [{"day_index": i, "topics": [{"topic_id": tid, "minutes": 20, "focus": "x"}],
              "summary": f"День {i}"} for i in range(1, 15)]
    llm = FakeLLM(response={"days": days})

    plan = await generate_plan(session, user, "math_base", llm)
    stored = json.loads(plan.days)
    assert len(stored) == 14


async def test_generate_plan_fallback_on_llm_error(session, seeded, user):
    """H2: network error → 14-day fallback plan, no crash."""
    llm = FakeLLM(raises=httpx.ConnectError("down"))

    plan = await generate_plan(session, user, "math_base", llm)
    assert isinstance(plan, LearningPlan)
    days = json.loads(plan.days)
    assert len(days) == 14


async def test_generate_plan_fallback_json_decode_error(session, seeded, user):
    """H2: JSONDecodeError → fallback plan returned."""
    llm = FakeLLM(raises=json.JSONDecodeError("bad", "", 0))
    plan = await generate_plan(session, user, "math_base", llm)
    days = json.loads(plan.days)
    assert len(days) == 14


async def test_generate_plan_uses_user_data(session, seeded, user, monkeypatch):
    """H1: user.grade, exam, goal are passed to prompt, not hardcoded."""
    captured = {}

    def fake_load_prompt(name, **vars):
        captured.update(vars)
        return [{"role": "user", "text": "ok"}]

    monkeypatch.setattr("app.services.plan.load_prompt", fake_load_prompt)
    llm = FakeLLM(response={"days": []})

    await generate_plan(session, user, "math_base", llm)
    assert captured.get("grade") == 11
    assert captured.get("exam") == "ЕГЭ"
    assert captured.get("goal") == "excellent"


async def test_generate_plan_prioritizes_weak_topics(session, seeded, user, monkeypatch):
    """Low mastery × high exam_weight → appears first in prompt."""
    topics = seeded["topics"][:3]
    # topic[0]: high mastery, high weight → low priority
    # topic[1]: low mastery, medium weight → high priority
    _seed_mastery(session, user, [topics[0], topics[1]], [0.9, 0.1])

    captured = {}

    def fake_load_prompt(name, **vars):
        captured.update(vars)
        return [{"role": "user", "text": "ok"}]

    monkeypatch.setattr("app.services.plan.load_prompt", fake_load_prompt)
    llm = FakeLLM(response={"days": []})

    await generate_plan(session, user, "math_base", llm)
    priority_text = captured.get("topics_priority", "")
    # topic[1] (low mastery) should appear before topic[0] (high mastery)
    idx_weak = priority_text.find(f"topic_id={topics[1].id}")
    idx_strong = priority_text.find(f"topic_id={topics[0].id}")
    assert idx_weak != -1 and idx_strong != -1
    assert idx_weak < idx_strong, "weak topic should have higher priority"


async def test_generate_plan_saves_to_db(session, seeded, user):
    llm = FakeLLM(response={"days": []})
    plan = await generate_plan(session, user, "math_base", llm)
    assert plan.id is not None
    assert plan.user_id == user.id
    assert plan.subject_code == "math_base"
