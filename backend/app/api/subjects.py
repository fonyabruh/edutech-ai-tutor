from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.db import get_session
from app.models import Mastery, Topic, User
from app.services.mastery import get_mastery_value

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("/{subject_code}/topics")
def get_topics(
    subject_code: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    topics = session.exec(select(Topic).where(Topic.subject_code == subject_code)).all()
    masteries = {
        m.topic_id: m
        for m in session.exec(select(Mastery).where(Mastery.user_id == user.id)).all()
    }
    return [
        {
            "id": t.id,
            "name": t.name,
            "codifier_code": t.codifier_code,
            "exam_weight": t.exam_weight,
            "mastery": get_mastery_value(masteries[t.id]) if t.id in masteries else 0.5,
        }
        for t in topics
    ]
