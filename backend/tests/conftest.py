from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models import Subject, Task, Topic, User

# ── JWT helpers ───────────────────────────────────────────────────────────────

def make_token(user_id: str, expired: bool = False) -> str:
    delta = timedelta(days=-1) if expired else timedelta(days=1)
    exp = datetime.now(UTC) + delta
    return jwt.encode({"sub": user_id, "exp": exp}, settings.jwt_secret, algorithm="HS256")


def auth(user_id: str) -> dict:
    return {"Authorization": f"Bearer {make_token(user_id)}"}


# ── DB fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng
    SQLModel.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Clear module-level state ──────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_lesson_sessions():
    from app.api import lesson
    lesson._sessions.clear()
    yield
    lesson._sessions.clear()


# ── Fake LLM ─────────────────────────────────────────────────────────────────

class FakeLLM:
    def __init__(self, response=None, raises=None, chunks=None):
        self.response = response
        self.raises = raises
        self.chunks = chunks or ["hello ", "world"]

    async def chat(self, messages, **kwargs):
        if self.raises:
            raise self.raises
        return self.response or {}

    async def stream(self, messages, **kwargs):
        for chunk in self.chunks:
            yield chunk


@pytest.fixture
def fake_llm():
    return FakeLLM()


# ── Seeded content ────────────────────────────────────────────────────────────

@pytest.fixture
def seeded(session):
    """Minimal deterministic content: 1 subject, 3 topics, varied tasks."""
    subj = Subject(code="math_base", name="Математика")
    session.add(subj)
    session.flush()

    def _t(name, code, w):
        return Topic(subject_code="math_base", name=name, codifier_code=code, exam_weight=w)

    t1 = _t("Алгебра", "mat.1.1", 0.3)
    t2 = _t("Геометрия", "mat.1.2", 0.25)
    t3 = _t("Вероятность", "mat.1.3", 0.15)
    t4 = _t("Функции", "mat.1.5", 0.12)
    t5 = _t("Неравенства", "mat.1.6", 0.1)
    t_small = _t("Малая тема", "mat.1.4", 0.1)
    session.add_all([t1, t2, t3, t4, t5, t_small])
    session.flush()

    tasks = []
    # t1: 6 tasks, difficulties 1 1 2 2 3 3
    for i, diff in enumerate([1, 1, 2, 2, 3, 3]):
        tasks.append(Task(
            subject_code="math_base", topic_id=t1.id, difficulty=diff,
            type="short_answer", statement_md=f"Задача t1-{i}",
            answer=f"ответ{i}", solution_md="решение",
        ))
    # t2: 4 tasks, difficulty 2
    for i in range(4):
        tasks.append(Task(
            subject_code="math_base", topic_id=t2.id, difficulty=2,
            type="multi_choice", statement_md=f"Задача t2-{i}",
            options='["А","Б","В"]', answer="А", solution_md="решение",
        ))
    # t3: 5 tasks mixed difficulty
    for i, diff in enumerate([1, 2, 2, 3, 3]):
        tasks.append(Task(
            subject_code="math_base", topic_id=t3.id, difficulty=diff,
            type="short_answer", statement_md=f"Задача t3-{i}",
            answer="42", solution_md="решение",
        ))
    # t4: 5 tasks difficulty 3
    for i in range(5):
        tasks.append(Task(
            subject_code="math_base", topic_id=t4.id, difficulty=3,
            type="short_answer", statement_md=f"Задача t4-{i}",
            answer="77", solution_md="решение",
        ))
    # t5: 3 tasks difficulty 3
    for i in range(3):
        tasks.append(Task(
            subject_code="math_base", topic_id=t5.id, difficulty=3,
            type="short_answer", statement_md=f"Задача t5-{i}",
            answer="88", solution_md="решение",
        ))
    # t_small: only 1 task (triggers H3 edge case)
    tasks.append(Task(
        subject_code="math_base", topic_id=t_small.id, difficulty=2,
        type="short_answer", statement_md="Малая задача",
        answer="1", solution_md="решение",
    ))

    session.add_all(tasks)
    session.commit()

    return {"subject": subj, "topics": [t1, t2, t3, t4, t5, t_small]}


@pytest.fixture
def user(session):
    u = User(device_id="test-device", grade=11, exam="ЕГЭ", goal="excellent",
             subjects="[]")
    session.add(u)
    session.commit()
    return u
