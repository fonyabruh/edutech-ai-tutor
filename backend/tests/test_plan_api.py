

from tests.conftest import FakeLLM, auth


def _make_days(topics):
    return [
        {"day_index": i, "topics": [{"topic_id": topics[0].id, "minutes": 20, "focus": "x"}],
         "summary": f"День {i}", "status": "available" if i == 1 else "locked"}
        for i in range(1, 15)
    ]


def test_generate_plan_endpoint(client, session, user, seeded, monkeypatch):
    fake = FakeLLM(response={"days": _make_days(seeded["topics"])})
    monkeypatch.setattr("app.api.plan.llm", fake)

    r = client.post("/plan/generate", headers=auth(user.id),
                    json={"subject_code": "math_base"})
    assert r.status_code == 200
    data = r.json()
    assert "days" in data
    assert len(data["days"]) == 14


def test_generate_plan_llm_error_fallback(client, session, user, seeded, monkeypatch):
    """H2: network error → 14-day fallback plan via API."""
    import httpx
    fake = FakeLLM(raises=httpx.ConnectError("down"))
    monkeypatch.setattr("app.api.plan.llm", fake)

    r = client.post("/plan/generate", headers=auth(user.id),
                    json={"subject_code": "math_base"})
    assert r.status_code == 200
    assert len(r.json()["days"]) == 14


def test_get_current_plan_not_found(client, user, seeded):
    r = client.get("/plan/current", headers=auth(user.id),
                   params={"subject_code": "math_base"})
    assert r.status_code == 404


def test_get_current_plan_returns_plan(client, session, user, seeded, monkeypatch):
    fake = FakeLLM(response={"days": _make_days(seeded["topics"])})
    monkeypatch.setattr("app.api.plan.llm", fake)
    client.post("/plan/generate", headers=auth(user.id),
                json={"subject_code": "math_base"})

    r = client.get("/plan/current", headers=auth(user.id),
                   params={"subject_code": "math_base"})
    assert r.status_code == 200
    assert r.json()["subject_code"] == "math_base"


def test_complete_day_updates_status(client, session, user, seeded, monkeypatch):
    fake = FakeLLM(response={"days": _make_days(seeded["topics"])})
    monkeypatch.setattr("app.api.plan.llm", fake)
    client.post("/plan/generate", headers=auth(user.id),
                json={"subject_code": "math_base"})

    r = client.post("/plan/day/1/complete", headers=auth(user.id),
                    params={"subject_code": "math_base"})
    assert r.status_code == 200

    plan_resp = client.get("/plan/current", headers=auth(user.id),
                           params={"subject_code": "math_base"})
    days = plan_resp.json()["days"]
    day1 = next(d for d in days if d["day_index"] == 1)
    assert day1["status"] == "complete"


def test_complete_day_no_plan_404(client, user, seeded):
    r = client.post("/plan/day/1/complete", headers=auth(user.id),
                    params={"subject_code": "math_base"})
    assert r.status_code == 404


def test_complete_day_later_index_iterates_past_earlier_days(
    client, session, user, seeded, monkeypatch
):
    """Mark day 5 complete — loop must iterate past days 1-4 (64->63 branch)."""
    fake = FakeLLM(response={"days": _make_days(seeded["topics"])})
    monkeypatch.setattr("app.api.plan.llm", fake)
    client.post("/plan/generate", headers=auth(user.id),
                json={"subject_code": "math_base"})

    r = client.post("/plan/day/5/complete", headers=auth(user.id),
                    params={"subject_code": "math_base"})
    assert r.status_code == 200

    days = client.get("/plan/current", headers=auth(user.id),
                      params={"subject_code": "math_base"}).json()["days"]
    day5 = next(d for d in days if d["day_index"] == 5)
    assert day5["status"] == "complete"


def test_complete_day_nonexistent_index_no_crash(client, session, user, seeded, monkeypatch):
    """Marking a day_index not in plan is a no-op, not a 500 (63->67 branch)."""
    fake = FakeLLM(response={"days": _make_days(seeded["topics"])})
    monkeypatch.setattr("app.api.plan.llm", fake)
    client.post("/plan/generate", headers=auth(user.id),
                json={"subject_code": "math_base"})

    r = client.post("/plan/day/99/complete", headers=auth(user.id),
                    params={"subject_code": "math_base"})
    assert r.status_code == 200
