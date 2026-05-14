import json

import httpx
from sqlmodel import select

from app.models import Attempt, DiagnosticResult, Mastery
from app.services.diagnostic import finalize_diagnostic, pick_diagnostic_tasks
from tests.conftest import FakeLLM

# ── pick_diagnostic_tasks ─────────────────────────────────────────────────────

def test_pick_tasks_returns_one_per_topic(session, seeded):
    tasks = pick_diagnostic_tasks(session, "math_base")
    topic_ids = [t.topic_id for t in tasks]
    assert len(topic_ids) == len(set(topic_ids)), "duplicate topics selected"


def test_pick_tasks_at_most_six(session, seeded):
    tasks = pick_diagnostic_tasks(session, "math_base")
    assert len(tasks) <= 6


def test_pick_tasks_fallback_when_difficulty_missing(session, seeded):
    """H6: if no task at target difficulty, falls back to any task for that topic."""
    topics = seeded["topics"]
    # t2 only has difficulty=2 tasks; pick_diagnostic_tasks may request diff=1 or 3
    tasks = pick_diagnostic_tasks(session, "math_base")
    # all returned tasks must belong to real topics
    valid_ids = {t.id for t in topics}
    for task in tasks:
        assert task.topic_id in valid_ids


def test_pick_tasks_difficulty_distribution(session, seeded):
    """H6: difficulty array is [1,1,2,2,2,3] — 2 easy, 3 medium, 1 hard."""

    counts = {1: 0, 2: 0, 3: 0}
    for _ in range(50):
        tasks = pick_diagnostic_tasks(session, "math_base")
        for t in tasks:
            counts[t.difficulty] = counts.get(t.difficulty, 0) + 1
    # Across 50 runs each yielding ≤6 tasks, easy/medium/hard should all appear
    assert counts[1] > 0
    assert counts[2] > 0
    assert counts[3] > 0


def test_pick_tasks_empty_subject_returns_empty(session, seeded):
    tasks = pick_diagnostic_tasks(session, "nonexistent_subject")
    assert tasks == []


# ── finalize_diagnostic ───────────────────────────────────────────────────────

async def _seed_attempts(session, user, seeded, session_id):
    topics = seeded["topics"]
    from sqlmodel import select as sel

    from app.models import Task
    tasks = session.exec(sel(Task).where(Task.topic_id == topics[0].id).limit(2)).all()
    for i, task in enumerate(tasks):
        session.add(Attempt(
            user_id=user.id, task_id=task.id, session_id=session_id,
            is_correct=(i == 0), is_diagnostic=True,
        ))
    session.flush()
    return tasks


async def test_finalize_diagnostic_updates_mastery(session, seeded, user):
    sid = "sess-1"
    llm = FakeLLM(response={
        "weak_topics": [{"topic_id": seeded["topics"][0].id, "comment": "слабо"}],
        "strong_topics": [],
        "priority_skills": [],
        "estimated_score": 50,
    })
    await _seed_attempts(session, user, seeded, sid)

    await finalize_diagnostic(session, user, "math_base", sid, llm)

    m = session.exec(
        select(Mastery).where(
            Mastery.user_id == user.id, Mastery.topic_id == seeded["topics"][0].id
        )
    ).first()
    assert m is not None
    assert m.alpha != 1.0 or m.beta != 1.0  # mastery was updated


async def test_finalize_diagnostic_uses_real_topic_ids(session, seeded, user):
    """B4: topic_ids from LLM response that don't exist are filtered out."""
    sid = "sess-b4"
    fake_id = 99999
    llm = FakeLLM(response={
        "weak_topics": [{"topic_id": fake_id, "comment": "фантомная"}],
        "strong_topics": [{"topic_id": seeded["topics"][0].id, "comment": "ок"}],
        "estimated_score": 40,
    })
    await _seed_attempts(session, user, seeded, sid)

    result = await finalize_diagnostic(session, user, "math_base", sid, llm)
    weak = json.loads(result.weak_topics)
    topic_ids = [w["topic_id"] for w in weak]
    assert fake_id not in topic_ids


async def test_finalize_diagnostic_llm_error_uses_mastery_fallback(session, seeded, user):
    """H2: LLM error → fallback computed from mastery, no exception propagated."""
    sid = "sess-h2"
    llm = FakeLLM(raises=httpx.ConnectError("timeout"))
    await _seed_attempts(session, user, seeded, sid)

    result = await finalize_diagnostic(session, user, "math_base", sid, llm)
    assert isinstance(result, DiagnosticResult)
    assert result.estimated_score is not None


async def test_finalize_diagnostic_json_decode_error_fallback(session, seeded, user):
    """H2: JSONDecodeError from LLM → fallback, not 500."""
    sid = "sess-json"
    llm = FakeLLM(raises=json.JSONDecodeError("bad json", "", 0))
    await _seed_attempts(session, user, seeded, sid)

    result = await finalize_diagnostic(session, user, "math_base", sid, llm)
    assert isinstance(result, DiagnosticResult)


async def test_finalize_diagnostic_uses_user_grade_exam(session, seeded, user, monkeypatch):
    """H1: user.grade / exam / goal are passed to load_prompt, not hardcoded."""
    sid = "sess-h1"
    captured = {}

    def fake_load_prompt(name, **vars):
        captured.update(vars)
        return [{"role": "user", "text": "ok"}]

    monkeypatch.setattr("app.services.diagnostic.load_prompt", fake_load_prompt)
    llm = FakeLLM(response={"estimated_score": 70})
    await _seed_attempts(session, user, seeded, sid)

    await finalize_diagnostic(session, user, "math_base", sid, llm)
    assert captured.get("grade") == 11
    assert captured.get("exam") == "ЕГЭ"
    assert captured.get("goal") == "excellent"


async def test_finalize_diagnostic_saves_priority_skills(session, seeded, user):
    sid = "sess-skills"
    skills = ["Квадратные уравнения", "Тригонометрия"]
    llm = FakeLLM(response={"priority_skills": skills, "estimated_score": 60})
    await _seed_attempts(session, user, seeded, sid)

    result = await finalize_diagnostic(session, user, "math_base", sid, llm)
    assert json.loads(result.priority_skills) == skills


async def test_finalize_diagnostic_null_answer_is_incorrect(session, seeded, user):
    """null user_answer (skip) → is_correct=False, mastery decreases beta."""
    sid = "sess-skip"
    from sqlmodel import select as sel

    from app.models import Task
    task = session.exec(sel(Task).where(Task.topic_id == seeded["topics"][0].id)).first()
    session.add(Attempt(
        user_id=user.id, task_id=task.id, session_id=sid,
        user_answer=None, is_correct=False, is_diagnostic=True,
    ))
    session.flush()

    llm = FakeLLM(response={"estimated_score": 30})
    await finalize_diagnostic(session, user, "math_base", sid, llm)
    m = session.exec(
        select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == task.topic_id)
    ).first()
    assert m.beta > 1.0


async def test_finalize_diagnostic_priority_skills_not_list_coerced(session, seeded, user):
    """If LLM returns priority_skills as non-list (e.g. string), it becomes [] (line 105)."""
    sid = "sess-ps-notlist"
    llm = FakeLLM(response={"priority_skills": "строка не список", "estimated_score": 55})
    await _seed_attempts(session, user, seeded, sid)

    result = await finalize_diagnostic(session, user, "math_base", sid, llm)
    assert json.loads(result.priority_skills) == []


async def test_finalize_diagnostic_attempt_with_deleted_task_skipped(session, seeded, user):
    """Attempt referencing a nonexistent task_id is skipped without crash (47->45 branch)."""
    sid = "sess-deleted-task"
    session.add(Attempt(
        user_id=user.id, task_id=99999, session_id=sid,
        is_correct=False, is_diagnostic=True,
    ))
    session.flush()

    llm = FakeLLM(response={"estimated_score": 40})
    result = await finalize_diagnostic(session, user, "math_base", sid, llm)
    assert result is not None


def test_pick_tasks_topic_with_no_tasks_skipped(session, seeded):
    """Topic with zero tasks is skipped in pick_diagnostic_tasks (25->18 branch)."""
    from app.models import Topic
    empty_topic = Topic(
        subject_code="math_base", name="Пустая тема",
        codifier_code="mat.0.0", exam_weight=0.05,
    )
    session.add(empty_topic)
    session.flush()

    tasks = pick_diagnostic_tasks(session, "math_base")
    for t in tasks:
        assert t.topic_id != empty_topic.id
