from app.models import Mastery
from tests.conftest import auth


def test_get_topics_returns_list(client, user, seeded):
    r = client.get("/subjects/math_base/topics", headers=auth(user.id))
    assert r.status_code == 200
    topics = r.json()
    assert isinstance(topics, list)
    assert len(topics) == len(seeded["topics"])


def test_get_topics_includes_mastery_field(client, user, seeded):
    r = client.get("/subjects/math_base/topics", headers=auth(user.id))
    for t in r.json():
        assert "mastery" in t
        assert 0.0 <= t["mastery"] <= 1.0


def test_get_topics_mastery_defaults_to_half_without_record(client, user, seeded):
    """No Mastery row → mastery = 0.5 (Beta(1,1))."""
    r = client.get("/subjects/math_base/topics", headers=auth(user.id))
    for t in r.json():
        assert t["mastery"] == 0.5


def test_get_topics_reflects_updated_mastery(client, session, user, seeded):
    topic = seeded["topics"][0]
    session.add(Mastery(user_id=user.id, topic_id=topic.id, alpha=9.0, beta=1.0))
    session.commit()

    r = client.get("/subjects/math_base/topics", headers=auth(user.id))
    found = next(t for t in r.json() if t["id"] == topic.id)
    assert abs(found["mastery"] - 0.9) < 0.01


def test_get_topics_empty_subject(client, user, seeded):
    r = client.get("/subjects/nonexistent/topics", headers=auth(user.id))
    assert r.status_code == 200
    assert r.json() == []
