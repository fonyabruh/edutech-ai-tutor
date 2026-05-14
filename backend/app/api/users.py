import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import onboarding_completed
from app.api.deps import get_current_user
from app.db import get_session
from app.models import Attempt, DiagnosticResult, Mastery, Subject, Topic, User

router = APIRouter(prefix="/me", tags=["users"])


class ProfilePatch(BaseModel):
    grade: int | None = None
    exam: str | None = None
    goal: str | None = None
    subjects: list[str] | None = None


def _user_response(user: User):
    return {
        "id": user.id,
        "grade": user.grade,
        "exam": user.exam,
        "goal": user.goal,
        "subjects": user.subjects,
        "created_at": user.created_at,
        "onboarding_completed": onboarding_completed(user),
    }


def _calc_streak(session, user_id):
    rows = session.exec(select(Attempt.created_at).where(Attempt.user_id == user_id)).all()
    days = {r.date() for r in rows}
    streak = 0
    check = date.today()
    while check in days:
        streak += 1
        check -= timedelta(days=1)
    return streak


@router.get("")
def get_me(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return {**_user_response(user), "streak": _calc_streak(session, user.id)}


@router.patch("")
def patch_me(
    body: ProfilePatch,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    old_subjects = set(json.loads(user.subjects or "[]"))
    if body.grade is not None:
        user.grade = body.grade
    if body.exam is not None:
        user.exam = body.exam
    if body.goal is not None:
        user.goal = body.goal
    if body.subjects is not None:
        user.subjects = json.dumps(body.subjects, ensure_ascii=False)
        new_subjects = set(body.subjects)
        added = new_subjects - old_subjects
        if added:
            topics = session.exec(
                select(Topic).where(Topic.subject_code.in_(list(added)))
            ).all()
            for topic in topics:
                exists = session.exec(
                    select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == topic.id)
                ).first()
                if not exists:
                    session.add(Mastery(user_id=user.id, topic_id=topic.id))
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_response(user)


@router.get("/subjects")
def get_subjects(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    codes = json.loads(user.subjects or "[]")
    result = []
    for code in codes:
        subj = session.exec(select(Subject).where(Subject.code == code)).first()
        if not subj:
            continue
        masteries = session.exec(
            select(Mastery).join(Topic).where(
                Mastery.user_id == user.id, Topic.subject_code == code
            )
        ).all()
        mastery_avg = (
            sum(m.alpha / (m.alpha + m.beta) for m in masteries) / len(masteries)
            if masteries
            else 0
        )
        last_result = session.exec(
            select(DiagnosticResult).where(
                DiagnosticResult.user_id == user.id, DiagnosticResult.subject_code == code
            ).order_by(DiagnosticResult.created_at.desc())
        ).first()
        result.append(
            {
                "code": code,
                "name": subj.name,
                "mastery_avg": mastery_avg,
                "last_session_at": last_result.created_at if last_result else None,
            }
        )
    return result
