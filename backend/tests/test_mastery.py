from sqlmodel import select

from app.models import Mastery
from app.services.mastery import get_mastery_value, update_mastery


def test_get_mastery_value_formula():
    m = Mastery(user_id="u", topic_id=1, alpha=3.0, beta=1.0)
    assert get_mastery_value(m) == 0.75


def test_get_mastery_value_default():
    m = Mastery(user_id="u", topic_id=1)
    assert get_mastery_value(m) == 0.5


def test_update_mastery_correct_increments_alpha(session, seeded, user):
    topic = seeded["topics"][0]
    m = update_mastery(session, user.id, topic.id, is_correct=True)
    assert m.alpha == 2.0
    assert m.beta == 1.0


def test_update_mastery_incorrect_increments_beta(session, seeded, user):
    topic = seeded["topics"][0]
    m = update_mastery(session, user.id, topic.id, is_correct=False)
    assert m.alpha == 1.0
    assert m.beta == 2.0


def test_update_mastery_no_duplicate_row(session, seeded, user):
    """M6: repeated calls update the same row, not create a new one."""
    topic = seeded["topics"][0]
    update_mastery(session, user.id, topic.id, is_correct=True)
    update_mastery(session, user.id, topic.id, is_correct=True)
    update_mastery(session, user.id, topic.id, is_correct=False)

    rows = session.exec(
        select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == topic.id)
    ).all()
    assert len(rows) == 1
    assert rows[0].alpha == 3.0
    assert rows[0].beta == 2.0


def test_update_mastery_creates_when_missing(session, seeded, user):
    topic = seeded["topics"][1]
    m = update_mastery(session, user.id, topic.id, is_correct=True)
    assert m.id is not None


def test_update_mastery_multiple_topics_no_cross(session, seeded, user):
    t1, t2 = seeded["topics"][0], seeded["topics"][1]
    update_mastery(session, user.id, t1.id, is_correct=True)
    update_mastery(session, user.id, t2.id, is_correct=False)

    m1 = session.exec(select(Mastery).where(Mastery.topic_id == t1.id)).first()
    m2 = session.exec(select(Mastery).where(Mastery.topic_id == t2.id)).first()
    assert m1.alpha == 2.0 and m1.beta == 1.0
    assert m2.alpha == 1.0 and m2.beta == 2.0
