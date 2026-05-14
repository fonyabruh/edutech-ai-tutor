from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Mastery


def update_mastery(session: Session, user_id: str, topic_id: int, is_correct: bool):
    m = session.exec(
        select(Mastery).where(Mastery.user_id == user_id, Mastery.topic_id == topic_id)
    ).first()
    if not m:
        m = Mastery(user_id=user_id, topic_id=topic_id)
        session.add(m)
    if is_correct:
        m.alpha += 1
    else:
        m.beta += 1
    m.updated_at = datetime.now(UTC)
    session.flush()
    return m


def get_mastery_value(m: Mastery) -> float:
    return m.alpha / (m.alpha + m.beta)
