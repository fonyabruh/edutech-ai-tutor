"""
Tests for chat API.
SSE streaming is complex to test in full; we test the synchronous parts
(GET /history, saved user message) and mock the stream for POST /message.
"""
from sqlmodel import select

from app.models import ChatMessage
from tests.conftest import FakeLLM, auth


def test_get_history_empty(client, user):
    r = client.get("/chat/history", headers=auth(user.id),
                   params={"subject_code": "math_base"})
    assert r.status_code == 200
    assert r.json() == []


def test_get_history_returns_messages(client, session, user):
    session.add(ChatMessage(user_id=user.id, subject_code="math_base",
                            role="user", content="Привет"))
    session.add(ChatMessage(user_id=user.id, subject_code="math_base",
                            role="assistant", content="Привет, ученик!"))
    session.commit()

    r = client.get("/chat/history", headers=auth(user.id),
                   params={"subject_code": "math_base"})
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"


def test_get_history_scoped_by_subject(client, session, user):
    session.add(ChatMessage(user_id=user.id, subject_code="math_base",
                            role="user", content="мат"))
    session.add(ChatMessage(user_id=user.id, subject_code="rus",
                            role="user", content="рус"))
    session.commit()

    r = client.get("/chat/history", headers=auth(user.id),
                   params={"subject_code": "math_base"})
    assert len(r.json()) == 1
    assert r.json()[0]["content"] == "мат"


def test_send_message_saves_user_message(client, session, user, seeded, monkeypatch):
    """POST /chat/message saves user message to DB before streaming."""
    fake = FakeLLM(chunks=["ответ"])
    monkeypatch.setattr("app.api.chat.llm", fake)

    # TestClient consumes the full SSE stream
    r = client.post("/chat/message", headers=auth(user.id),
                    json={"subject_code": "math_base", "message": "Привет!"})
    assert r.status_code == 200

    msgs = session.exec(
        select(ChatMessage).where(
            ChatMessage.user_id == user.id,
            ChatMessage.role == "user",
        )
    ).all()
    assert any(m.content == "Привет!" for m in msgs)


def test_get_history_limited_to_50(client, session, user):
    for i in range(60):
        session.add(ChatMessage(user_id=user.id, subject_code="math_base",
                                role="user", content=f"msg {i}"))
    session.commit()

    r = client.get("/chat/history", headers=auth(user.id),
                   params={"subject_code": "math_base"})
    assert len(r.json()) == 50


def test_send_message_with_diagnostic_result_uses_weak_topics(
    client, session, user, seeded, monkeypatch
):
    """When a DiagnosticResult exists, weak topics are passed to the prompt (lines 74-76)."""
    import json

    from app.models import DiagnosticResult
    topic = seeded["topics"][0]
    session.add(DiagnosticResult(
        user_id=user.id,
        subject_code="math_base",
        weak_topics=json.dumps([{"topic_id": topic.id, "comment": "слабо"}]),
        strong_topics="[]",
        priority_skills="[]",
        estimated_score=50,
    ))
    session.commit()

    fake = FakeLLM(chunks=["ответ"])
    monkeypatch.setattr("app.api.chat.llm", fake)

    r = client.post("/chat/message", headers=auth(user.id),
                    json={"subject_code": "math_base", "message": "Помоги с алгеброй"})
    assert r.status_code == 200


def test_send_message_stream_error_yields_error_event(client, session, user, seeded, monkeypatch):
    """If llm.stream raises inside SSE, event: error is emitted, not 500."""

    class ErrorLLM:
        async def stream(self, messages, **kwargs):
            raise RuntimeError("LLM down")
            yield  # makes this an async generator

    monkeypatch.setattr("app.api.chat.llm", ErrorLLM())

    r = client.post("/chat/message", headers=auth(user.id),
                    json={"subject_code": "math_base", "message": "Привет!"})
    assert r.status_code == 200
    assert "event: error" in r.text
