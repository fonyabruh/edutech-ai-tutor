import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.config import settings
from app.db import get_session
from app.llm.client import LLMClient
from app.models import Attempt, DiagnosticResult, Task, User
from app.services.diagnostic import finalize_diagnostic, pick_diagnostic_tasks

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])
llm = LLMClient(settings)


class StartRequest(BaseModel):
    subject_code: str


class AnswerRequest(BaseModel):
    session_id: str
    task_id: int
    user_answer: str | None = None


class FinishRequest(BaseModel):
    session_id: str
    subject_code: str


def _task_payload(task: Task):
    return {
        "id": task.id,
        "statement_md": task.statement_md,
        "type": task.type,
        "options": json.loads(task.options) if task.options else None,
    }


@router.post("/start")
async def start_diagnostic(
    body: StartRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    tasks = pick_diagnostic_tasks(session, body.subject_code)
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found for this subject")
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "tasks": [_task_payload(t) for t in tasks],
        "total": len(tasks),
    }


@router.post("/answer")
async def answer_diagnostic(
    body: AnswerRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    task = session.exec(select(Task).where(Task.id == body.task_id)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    is_correct = (body.user_answer or "").strip().lower() == task.answer.strip().lower()
    attempt = Attempt(
        user_id=user.id,
        task_id=body.task_id,
        session_id=body.session_id,
        user_answer=body.user_answer,
        is_correct=is_correct,
        is_diagnostic=True,
    )
    session.add(attempt)
    session.commit()
    return {"saved": True}


@router.post("/finish")
async def finish_diagnostic(
    body: FinishRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    result = await finalize_diagnostic(session, user, body.subject_code, body.session_id, llm)
    return {
        "id": result.id,
        "subject_code": result.subject_code,
        "weak_topics": json.loads(result.weak_topics),
        "strong_topics": json.loads(result.strong_topics),
        "priority_skills": json.loads(result.priority_skills),
        "estimated_score": result.estimated_score,
        "llm_summary": result.llm_summary,
        "created_at": result.created_at,
    }


@router.get("/result/{subject_code}")
async def get_diagnostic_result(
    subject_code: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    result = session.exec(
        select(DiagnosticResult)
        .where(DiagnosticResult.user_id == user.id, DiagnosticResult.subject_code == subject_code)
        .order_by(DiagnosticResult.created_at.desc())
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="No diagnostic result found")
    return {
        "id": result.id,
        "subject_code": result.subject_code,
        "weak_topics": json.loads(result.weak_topics),
        "strong_topics": json.loads(result.strong_topics),
        "priority_skills": json.loads(result.priority_skills),
        "estimated_score": result.estimated_score,
        "llm_summary": result.llm_summary,
        "created_at": result.created_at,
    }
