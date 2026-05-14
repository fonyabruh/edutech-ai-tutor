
from sqlmodel import select

from app.models import Attempt
from tests.conftest import FakeLLM, auth


def test_start_diagnostic_returns_session_and_tasks(client, user, seeded):
    r = client.post("/diagnostic/start", headers=auth(user.id),
                    json={"subject_code": "math_base"})
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert isinstance(data["tasks"], list)
    assert len(data["tasks"]) > 0


def test_start_diagnostic_no_tasks_404(client, user, seeded):
    r = client.post("/diagnostic/start", headers=auth(user.id),
                    json={"subject_code": "nonexistent"})
    assert r.status_code == 404


def test_answer_diagnostic_saves_attempt(client, session, user, seeded):
    start = client.post("/diagnostic/start", headers=auth(user.id),
                        json={"subject_code": "math_base"}).json()
    task_id = start["tasks"][0]["id"]
    session_id = start["session_id"]

    r = client.post("/diagnostic/answer", headers=auth(user.id),
                    json={"session_id": session_id, "task_id": task_id,
                          "user_answer": "ответ0"})
    assert r.status_code == 200
    attempt = session.exec(
        select(Attempt).where(Attempt.session_id == session_id)
    ).first()
    assert attempt is not None


def test_answer_diagnostic_correct_answer_case_insensitive(client, session, user, seeded):
    """Answer comparison is case-insensitive and trims whitespace."""
    start = client.post("/diagnostic/start", headers=auth(user.id),
                        json={"subject_code": "math_base"}).json()
    # find task with known answer
    task_id = start["tasks"][0]["id"]
    from sqlmodel import select as sel

    from app.models import Task
    task = session.exec(sel(Task).where(Task.id == task_id)).first()

    r = client.post("/diagnostic/answer", headers=auth(user.id),
                    json={"session_id": start["session_id"], "task_id": task_id,
                          "user_answer": task.answer.upper() + "  "})
    assert r.status_code == 200
    attempt = session.exec(
        select(Attempt).where(Attempt.task_id == task_id)
    ).first()
    assert attempt.is_correct is True


def test_answer_diagnostic_null_answer_is_incorrect(client, session, user, seeded):
    """B: null user_answer (skip) → is_correct=False, no exception."""
    start = client.post("/diagnostic/start", headers=auth(user.id),
                        json={"subject_code": "math_base"}).json()
    task_id = start["tasks"][0]["id"]

    r = client.post("/diagnostic/answer", headers=auth(user.id),
                    json={"session_id": start["session_id"], "task_id": task_id,
                          "user_answer": None})
    assert r.status_code == 200
    attempt = session.exec(
        select(Attempt).where(Attempt.task_id == task_id)
    ).first()
    assert attempt.is_correct is False


def test_finish_diagnostic_returns_result(client, session, user, seeded, monkeypatch):
    fake = FakeLLM(response={
        "weak_topics": [{"topic_id": seeded["topics"][0].id, "comment": "слабо"}],
        "strong_topics": [],
        "priority_skills": ["навык 1"],
        "estimated_score": 55,
        "overall_comment": "всё ок",
    })
    monkeypatch.setattr("app.api.diagnostic.llm", fake)

    start = client.post("/diagnostic/start", headers=auth(user.id),
                        json={"subject_code": "math_base"}).json()
    sid = start["session_id"]
    for t in start["tasks"]:
        client.post("/diagnostic/answer", headers=auth(user.id),
                    json={"session_id": sid, "task_id": t["id"], "user_answer": None})

    r = client.post("/diagnostic/finish", headers=auth(user.id),
                    json={"session_id": sid, "subject_code": "math_base"})
    assert r.status_code == 200
    data = r.json()
    assert "estimated_score" in data
    assert isinstance(data["weak_topics"], list)
    assert isinstance(data["priority_skills"], list)


def test_finish_diagnostic_topic_ids_are_real(client, session, user, seeded, monkeypatch):
    """B4: fake topic_id from LLM gets filtered out."""
    fake = FakeLLM(response={
        "weak_topics": [{"topic_id": 99999, "comment": "phantom"}],
        "strong_topics": [],
        "estimated_score": 40,
    })
    monkeypatch.setattr("app.api.diagnostic.llm", fake)

    start = client.post("/diagnostic/start", headers=auth(user.id),
                        json={"subject_code": "math_base"}).json()
    sid = start["session_id"]
    for t in start["tasks"]:
        client.post("/diagnostic/answer", headers=auth(user.id),
                    json={"session_id": sid, "task_id": t["id"], "user_answer": None})

    r = client.post("/diagnostic/finish", headers=auth(user.id),
                    json={"session_id": sid, "subject_code": "math_base"})
    weak = r.json()["weak_topics"]
    assert all(w["topic_id"] != 99999 for w in weak)


def test_get_diagnostic_result_not_found(client, user, seeded):
    r = client.get("/diagnostic/result/math_base", headers=auth(user.id))
    assert r.status_code == 404


def test_get_diagnostic_result_returns_latest(client, session, user, seeded, monkeypatch):
    fake = FakeLLM(response={"estimated_score": 60})
    monkeypatch.setattr("app.api.diagnostic.llm", fake)

    start = client.post("/diagnostic/start", headers=auth(user.id),
                        json={"subject_code": "math_base"}).json()
    sid = start["session_id"]
    for t in start["tasks"]:
        client.post("/diagnostic/answer", headers=auth(user.id),
                    json={"session_id": sid, "task_id": t["id"], "user_answer": None})
    client.post("/diagnostic/finish", headers=auth(user.id),
                json={"session_id": sid, "subject_code": "math_base"})

    r = client.get("/diagnostic/result/math_base", headers=auth(user.id))
    assert r.status_code == 200
    assert r.json()["subject_code"] == "math_base"


def test_answer_diagnostic_task_not_found_404(client, user, seeded):
    """POST /diagnostic/answer with nonexistent task_id → 404."""
    r = client.post("/diagnostic/answer", headers=auth(user.id),
                    json={"session_id": "some-sid", "task_id": 99999,
                          "user_answer": "x"})
    assert r.status_code == 404
