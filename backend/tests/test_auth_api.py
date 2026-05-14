
from sqlmodel import select

from app.models import User
from tests.conftest import auth, make_token


def test_anonymous_auth_creates_user(client, session):
    r = client.post("/auth/anonymous", json={"device_id": "dev-abc"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["onboarding_completed"] is False
    u = session.exec(select(User).where(User.device_id == "dev-abc")).first()
    assert u is not None


def test_anonymous_auth_returns_same_user_on_repeat(client, session):
    """Duplicate device_id → same user returned, not a new one."""
    r1 = client.post("/auth/anonymous", json={"device_id": "dev-dup"})
    r2 = client.post("/auth/anonymous", json={"device_id": "dev-dup"})
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]
    count = session.exec(select(User).where(User.device_id == "dev-dup")).all()
    assert len(count) == 1


def test_anonymous_auth_includes_onboarding_completed(client, session):
    r = client.post("/auth/anonymous", json={"device_id": "dev-onboard"})
    assert "onboarding_completed" in r.json()["user"]


def test_anonymous_auth_goal_in_response(client, session):
    r = client.post("/auth/anonymous", json={"device_id": "dev-goal"})
    assert "goal" in r.json()["user"]


def test_invalid_token_returns_401(client):
    r = client.get("/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401


def test_expired_token_returns_401(client, user):
    token = make_token(user.id, expired=True)
    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_missing_token_returns_4xx(client):
    r = client.get("/me")
    assert r.status_code in (401, 403)


def test_deleted_user_returns_401(client, session):
    """Valid JWT but user removed from DB → 401."""
    u = User(device_id="dev-ghost")
    session.add(u)
    session.commit()
    token = make_token(u.id)
    session.delete(u)
    session.commit()

    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_get_me_returns_user(client, user):
    r = client.get("/me", headers=auth(user.id))
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == user.id
    assert data["grade"] == 11
    assert data["exam"] == "ЕГЭ"
    assert "streak" in data


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
