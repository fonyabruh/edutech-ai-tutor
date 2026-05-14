
from sqlmodel import select

from app.models import Mastery, Topic
from tests.conftest import auth


def test_patch_me_updates_grade_exam_goal(client, user):
    r = client.patch("/me", headers=auth(user.id),
                     json={"grade": 10, "exam": "ОГЭ", "goal": "min"})
    assert r.status_code == 200
    data = r.json()
    assert data["grade"] == 10
    assert data["exam"] == "ОГЭ"
    assert data["goal"] == "min"


def test_patch_me_creates_mastery_for_new_subjects(client, session, user, seeded):
    """PATCH /me adding a subject creates Mastery rows for all its topics."""
    r = client.patch("/me", headers=auth(user.id), json={"subjects": ["math_base"]})
    assert r.status_code == 200

    topics = session.exec(select(Topic).where(Topic.subject_code == "math_base")).all()
    masteries = session.exec(select(Mastery).where(Mastery.user_id == user.id)).all()
    assert len(masteries) == len(topics)


def test_patch_me_no_duplicate_mastery_on_re_patch(client, session, user, seeded):
    """M6: sending same subjects twice must not duplicate Mastery rows."""
    client.patch("/me", headers=auth(user.id), json={"subjects": ["math_base"]})
    client.patch("/me", headers=auth(user.id), json={"subjects": ["math_base"]})

    masteries = session.exec(select(Mastery).where(Mastery.user_id == user.id)).all()
    topic_ids = [m.topic_id for m in masteries]
    assert len(topic_ids) == len(set(topic_ids)), "duplicate Mastery rows found"


def test_patch_me_returns_onboarding_completed_false_when_missing(client, user):
    r = client.patch("/me", headers=auth(user.id), json={"grade": 11})
    assert r.json()["onboarding_completed"] is False


def test_patch_me_returns_onboarding_completed_true_when_full(client, user, seeded):
    r = client.patch("/me", headers=auth(user.id),
                     json={"grade": 11, "exam": "ЕГЭ",
                           "subjects": ["math_base"], "goal": "excellent"})
    assert r.json()["onboarding_completed"] is True


def test_get_subjects_returns_list(client, user, seeded):
    # First patch to set subjects so /me/subjects has something
    client.patch("/me", headers=auth(user.id), json={"subjects": ["math_base"]})
    r = client.get("/me/subjects", headers=auth(user.id))
    assert r.status_code == 200
    subjects = r.json()
    assert isinstance(subjects, list)
    assert any(s["code"] == "math_base" for s in subjects)
    assert "mastery_avg" in subjects[0]


def test_get_subjects_mastery_avg_without_mastery_records(client, session, user, seeded):
    """With no Mastery rows yet, mastery_avg should still be 0 (not crash)."""
    client.patch("/me", headers=auth(user.id), json={"subjects": ["math_base"]})
    # Remove mastery rows so mastery_avg has no input
    from sqlmodel import delete

    from app.models import Mastery as M
    session.exec(delete(M).where(M.user_id == user.id))
    session.commit()

    r = client.get("/me/subjects", headers=auth(user.id))
    assert r.status_code == 200
    assert r.json()[0]["mastery_avg"] == 0


def test_get_me_streak_zero_when_no_attempts(client, user):
    r = client.get("/me", headers=auth(user.id))
    assert r.json()["streak"] == 0


def test_get_me_streak_positive_with_today_attempt(client, session, user, seeded):
    """Streak is >= 1 when user has an Attempt created today."""
    from sqlmodel import select as sel

    from app.models import Attempt, Task
    task = session.exec(sel(Task).where(Task.topic_id == seeded["topics"][0].id)).first()
    session.add(Attempt(user_id=user.id, task_id=task.id, session_id="s1", is_correct=True))
    session.commit()

    r = client.get("/me", headers=auth(user.id))
    assert r.json()["streak"] >= 1


def test_get_subjects_ignores_unknown_subject_code(client, session, user):
    """If user.subjects contains a code not in DB, it is silently skipped."""
    import json

    from sqlmodel import select as sel

    from app.models import User
    u = session.exec(sel(User).where(User.id == user.id)).first()
    u.subjects = json.dumps(["does_not_exist"])
    session.commit()

    r = client.get("/me/subjects", headers=auth(user.id))
    assert r.status_code == 200
    assert r.json() == []


def test_patch_me_skips_creating_mastery_when_row_already_exists(client, session, user, seeded):
    """If Mastery already exists for a topic, PATCH must not create a duplicate (76->72 branch)."""
    topic = seeded["topics"][0]
    session.add(Mastery(user_id=user.id, topic_id=topic.id))
    session.commit()

    r = client.patch("/me", headers=auth(user.id), json={"subjects": ["math_base"]})
    assert r.status_code == 200

    masteries = session.exec(select(Mastery).where(Mastery.user_id == user.id)).all()
    ids = [m.topic_id for m in masteries]
    assert len(ids) == len(set(ids)), "duplicate Mastery rows found"
