
from sqlmodel import select

from app.models import Attempt, Mastery, Task
from tests.conftest import FakeLLM, auth


def _start_lesson(client, user, seeded, topic_idx=0):
    topic = seeded["topics"][topic_idx]
    r = client.post("/lesson/start", headers=auth(user.id),
                    json={"subject_code": "math_base", "topic_id": topic.id})
    assert r.status_code == 200
    return r.json(), topic


def test_start_lesson_returns_tasks(client, user, seeded):
    data, topic = _start_lesson(client, user, seeded)
    assert "lesson_id" in data
    assert "tasks" in data
    assert len(data["tasks"]) > 0
    assert "theory_md" in data


def test_start_lesson_small_topic_no_crash(client, user, seeded):
    """H3: topic with 1 task → start succeeds with 1 task, no ValueError."""
    data, _ = _start_lesson(client, user, seeded, topic_idx=5)  # t_small
    assert data["lesson_id"]
    assert len(data["tasks"]) == 1


def test_start_lesson_max_four_tasks(client, user, seeded):
    data, _ = _start_lesson(client, user, seeded, topic_idx=0)  # t1 has 6 tasks
    assert len(data["tasks"]) <= 4


def test_answer_lesson_correct_answer(client, session, user, seeded):
    data, topic = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]
    task = data["tasks"][0]

    from sqlmodel import select as sel

    from app.models import Task
    db_task = session.exec(sel(Task).where(Task.id == task["id"])).first()

    r = client.post("/lesson/answer", headers=auth(user.id),
                    json={"lesson_id": lid, "task_id": task["id"],
                          "user_answer": db_task.answer})
    assert r.status_code == 200
    assert r.json()["is_correct"] is True


def test_answer_lesson_case_insensitive(client, session, user, seeded):
    """Answer comparison strips whitespace and is case-insensitive."""
    data, _ = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]
    task_id = data["tasks"][0]["id"]

    from sqlmodel import select as sel

    from app.models import Task
    db_task = session.exec(sel(Task).where(Task.id == task_id)).first()

    r = client.post("/lesson/answer", headers=auth(user.id),
                    json={"lesson_id": lid, "task_id": task_id,
                          "user_answer": "  " + db_task.answer.upper() + " "})
    assert r.json()["is_correct"] is True


def test_answer_lesson_wrong_answer(client, user, seeded):
    data, _ = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]
    task_id = data["tasks"][0]["id"]

    r = client.post("/lesson/answer", headers=auth(user.id),
                    json={"lesson_id": lid, "task_id": task_id,
                          "user_answer": "completely wrong answer xyz"})
    assert r.json()["is_correct"] is False


def test_answer_lesson_no_correct_answer_in_response(client, user, seeded):
    """M7: correct_answer must not leak in /lesson/answer response."""
    data, _ = _start_lesson(client, user, seeded)
    r = client.post("/lesson/answer", headers=auth(user.id),
                    json={"lesson_id": data["lesson_id"],
                          "task_id": data["tasks"][0]["id"],
                          "user_answer": "x"})
    assert "correct_answer" not in r.json()


def test_answer_lesson_saves_attempt_and_updates_mastery(client, session, user, seeded):
    data, topic = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]
    task_id = data["tasks"][0]["id"]

    client.post("/lesson/answer", headers=auth(user.id),
                json={"lesson_id": lid, "task_id": task_id, "user_answer": "wrong"})

    attempt = session.exec(
        select(Attempt).where(Attempt.session_id == lid, Attempt.task_id == task_id)
    ).first()
    assert attempt is not None

    mastery = session.exec(
        select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == topic.id)
    ).first()
    assert mastery is not None


def test_finish_lesson_returns_stats(client, session, user, seeded):
    data, topic = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]

    from sqlmodel import select as sel

    from app.models import Task
    db_task = session.exec(sel(Task).where(Task.id == data["tasks"][0]["id"])).first()

    client.post("/lesson/answer", headers=auth(user.id),
                json={"lesson_id": lid, "task_id": data["tasks"][0]["id"],
                      "user_answer": db_task.answer})

    r = client.post("/lesson/finish", headers=auth(user.id),
                    json={"lesson_id": lid})
    assert r.status_code == 200
    result = r.json()
    assert result["tasks_total"] >= 1
    assert result["correct"] >= 1
    assert "mastery_before" in result
    assert "mastery_after" in result
    assert "xp_earned" in result


def test_finish_lesson_unknown_lesson_id_no_crash(client, user, seeded):
    """H9: unknown lesson_id (server restarted) → 200 with zeros, not 500."""
    r = client.post("/lesson/finish", headers=auth(user.id),
                    json={"lesson_id": "nonexistent-lesson-id"})
    assert r.status_code == 200
    data = r.json()
    assert data["tasks_total"] == 0
    assert data["correct"] == 0


def test_finish_lesson_fallback_from_attempts(client, session, user, seeded):
    """H9: after session dict cleared, finish reconstructs from Attempt records."""
    from app.api import lesson as lesson_mod

    data, topic = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]

    from sqlmodel import select as sel

    from app.models import Task
    db_task = session.exec(sel(Task).where(Task.id == data["tasks"][0]["id"])).first()

    client.post("/lesson/answer", headers=auth(user.id),
                json={"lesson_id": lid, "task_id": db_task.id,
                      "user_answer": db_task.answer})

    # Simulate server restart: clear in-memory session
    lesson_mod._sessions.clear()

    r = client.post("/lesson/finish", headers=auth(user.id),
                    json={"lesson_id": lid})
    assert r.status_code == 200
    result = r.json()
    assert result["tasks_total"] == 1
    assert result["correct"] == 1


def test_explain_endpoint_streams_sse(client, session, user, seeded, monkeypatch):
    """POST /lesson/explain returns SSE stream with chunk and done events."""
    from sqlmodel import select as sel

    from app.models import Task

    fake = FakeLLM(chunks=["разбор ", "ошибки"])
    monkeypatch.setattr("app.api.lesson.llm", fake)

    real_task = session.exec(
        sel(Task).where(Task.topic_id == seeded["topics"][0].id)
    ).first()

    r = client.post("/lesson/explain", headers=auth(user.id),
                    json={"task_id": real_task.id, "user_answer": "неверно"})
    assert r.status_code == 200
    assert "event: chunk" in r.text or "event: done" in r.text


def test_explain_task_not_found(client, user, seeded, monkeypatch):
    r = client.post("/lesson/explain", headers=auth(user.id),
                    json={"task_id": 99999, "user_answer": "x"})
    assert r.status_code == 404


def test_mastery_increases_on_correct_answer(client, session, user, seeded):
    """Correct answers should not decrease mastery."""
    data, topic = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]

    from sqlmodel import select as sel

    from app.models import Task
    db_task = session.exec(sel(Task).where(Task.id == data["tasks"][0]["id"])).first()

    client.post("/lesson/answer", headers=auth(user.id),
                json={"lesson_id": lid, "task_id": db_task.id,
                      "user_answer": db_task.answer})

    result = client.post("/lesson/finish", headers=auth(user.id),
                         json={"lesson_id": lid}).json()
    assert result["mastery_after"] >= result["mastery_before"]


def test_start_lesson_unknown_topic_404(client, user, seeded):
    """POST /lesson/start with nonexistent topic_id → 404."""
    r = client.post("/lesson/start", headers=auth(user.id),
                    json={"subject_code": "math_base", "topic_id": 99999})
    assert r.status_code == 404


def test_start_lesson_enough_tasks_skips_fallback(client, user, seeded):
    """topic_idx=1 (t2: 4 tasks diff=2) with default mastery 0.5 → target_diff=2,
    len(by_diff)==4, no fallback to all_tasks needed."""
    data, _ = _start_lesson(client, user, seeded, topic_idx=1)
    assert len(data["tasks"]) == 4


def test_answer_lesson_task_not_found_404(client, user, seeded):
    """POST /lesson/answer with nonexistent task_id → 404."""
    data, _ = _start_lesson(client, user, seeded)
    r = client.post("/lesson/answer", headers=auth(user.id),
                    json={"lesson_id": data["lesson_id"], "task_id": 99999,
                          "user_answer": "x"})
    assert r.status_code == 404


def test_answer_lesson_without_active_session(client, session, user, seeded):
    """Answer submitted after session evicted from _sessions dict → still 200."""
    from app.api import lesson as lesson_mod

    data, _ = _start_lesson(client, user, seeded)
    lid = data["lesson_id"]
    task_id = data["tasks"][0]["id"]

    lesson_mod._sessions.clear()

    r = client.post("/lesson/answer", headers=auth(user.id),
                    json={"lesson_id": lid, "task_id": task_id, "user_answer": "x"})
    assert r.status_code == 200
    assert "is_correct" in r.json()


def test_explain_stream_error_yields_error_event(client, session, user, seeded, monkeypatch):
    """If llm.stream raises, /lesson/explain yields event: error, not 500."""

    class ErrorLLM:
        async def stream(self, messages, **kwargs):
            raise RuntimeError("stream broke")
            yield  # makes this an async generator

    monkeypatch.setattr("app.api.lesson.llm", ErrorLLM())

    task = session.exec(select(Task).where(Task.topic_id == seeded["topics"][0].id)).first()
    r = client.post("/lesson/explain", headers=auth(user.id),
                    json={"task_id": task.id, "user_answer": "неверно"})
    assert r.status_code == 200
    assert "event: error" in r.text

