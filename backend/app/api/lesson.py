import json
import random
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.config import settings
from app.db import get_session
from app.llm.client import LLMClient
from app.llm.prompts import load_prompt
from app.models import Attempt, Mastery, Task, Topic, User
from app.services.mastery import get_mastery_value, update_mastery

router = APIRouter(prefix="/lesson", tags=["lesson"])
llm = LLMClient(settings)

_sessions: dict[str, dict] = {}


class StartRequest(BaseModel):
    subject_code: str
    topic_id: int


class AnswerRequest(BaseModel):
    lesson_id: str
    task_id: int
    user_answer: str


class FinishRequest(BaseModel):
    lesson_id: str


class ExplainRequest(BaseModel):
    task_id: int
    user_answer: str


@router.post("/start")
def start_lesson(
    body: StartRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    topic = session.exec(select(Topic).where(Topic.id == body.topic_id)).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    mastery_obj = session.exec(
        select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == body.topic_id)
    ).first()
    mastery_val = get_mastery_value(mastery_obj) if mastery_obj else 0.5
    target_diff = max(1, min(4, int(mastery_val * 5)))

    all_tasks = session.exec(select(Task).where(Task.topic_id == body.topic_id)).all()
    by_diff = [t for t in all_tasks if t.difficulty == target_diff]
    if len(by_diff) < 4:
        by_diff = all_tasks
    tasks = random.sample(by_diff, min(4, len(by_diff)))

    lesson_id = str(uuid.uuid4())
    _sessions[lesson_id] = {
        "user_id": user.id,
        "topic_id": body.topic_id,
        "tasks": [t.id for t in tasks],
        "mastery_before": mastery_val,
        "correct": 0,
        "total": 0,
    }

    return {
        "lesson_id": lesson_id,
        "theory_md": topic.theory_md or f"**{topic.name}**\n\nТеория по данной теме.",
        "tasks": [
            {
                "id": t.id,
                "statement_md": t.statement_md,
                "type": t.type,
                "options": json.loads(t.options) if t.options else None,
                "difficulty": t.difficulty,
            }
            for t in tasks
        ],
    }


@router.post("/answer")
def answer_lesson(
    body: AnswerRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    task = session.exec(select(Task).where(Task.id == body.task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    is_correct = body.user_answer.strip().lower() == task.answer.strip().lower()
    attempt = Attempt(
        user_id=user.id,
        task_id=body.task_id,
        session_id=body.lesson_id,
        user_answer=body.user_answer,
        is_correct=is_correct,
        is_diagnostic=False,
    )
    session.add(attempt)
    update_mastery(session, user.id, task.topic_id, is_correct)
    session.commit()

    if body.lesson_id in _sessions:
        s = _sessions[body.lesson_id]
        s["total"] += 1
        if is_correct:
            s["correct"] += 1

    return {"is_correct": is_correct}


@router.post("/finish")
def finish_lesson(
    body: FinishRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    s = _sessions.pop(body.lesson_id, {})
    topic_id = s.get("topic_id")
    mastery_before = s.get("mastery_before", 0)

    # fallback: compute from attempts when in-memory session was lost
    if not s:
        attempts = session.exec(
            select(Attempt).where(Attempt.user_id == user.id, Attempt.session_id == body.lesson_id)
        ).all()
        correct = sum(1 for a in attempts if a.is_correct)
        total = len(attempts)
        if attempts:
            task = session.exec(select(Task).where(Task.id == attempts[0].task_id)).first()
            topic_id = task.topic_id if task else None
    else:
        correct = s.get("correct", 0)
        total = s.get("total", 0)

    mastery_after = mastery_before
    if topic_id:
        m = session.exec(
            select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == topic_id)
        ).first()
        mastery_after = get_mastery_value(m) if m else mastery_before

    return {
        "tasks_total": total,
        "correct": correct,
        "mastery_before": mastery_before,
        "mastery_after": mastery_after,
        "xp_earned": correct * 10,
    }


@router.post("/explain")
async def explain(
    body: ExplainRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    task = session.exec(select(Task).where(Task.id == body.task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    topic = session.exec(select(Topic).where(Topic.id == task.topic_id)).first()

    msgs = load_prompt(
        "explain_error",
        topic_name=topic.name if topic else "неизвестная тема",
        statement=task.statement_md,
        solution=task.solution_md,
        correct_answer=task.answer,
        user_answer=body.user_answer,
    )

    async def sse_stream():
        try:
            async for chunk in llm.stream(msgs):
                data = json.dumps({"text": chunk}, ensure_ascii=False)
                yield f"event: chunk\ndata: {data}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


    return StreamingResponse(sse_stream(), media_type="text/event-stream")
