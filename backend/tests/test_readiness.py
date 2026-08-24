def test_readiness_score_insufficient_with_no_data(client, registered_user):
    """With zero assessment signals, the composite score must be honestly
    reported as unavailable (None) - never a fabricated 0/100, which would
    look like a real (terrible) measured score rather than "not assessed"."""
    res = client.post("/api/v1/readiness/compute", headers=registered_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["composite_score"] is None
    assert body["data_status"] == "insufficient"
    assert body["breakdown"]["components_used"] == []
    # every dimension should be explicitly null ("Not Assessed"), not 0
    for dim in ["dsa", "cs_fundamentals", "aptitude", "communication", "resume", "interview", "company_prep"]:
        assert body["breakdown"][dim] is None


def test_readiness_score_uses_quiz_only_when_no_resume(client, registered_user):
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 80},
                headers=registered_user["headers"])
    client.post("/api/v1/quiz/submit", json={"subject": "DBMS", "score_percent": 60},
                headers=registered_user["headers"])

    res = client.post("/api/v1/readiness/compute", headers=registered_user["headers"])
    body = res.json()
    # DSA (80, weight 25%) + DBMS (60, weight 15%) re-normalized = 72.5 -> 73
    assert body["composite_score"] in (72, 73)
    assert any(c in body["breakdown"]["components_used"] for c in ["dsa", "cs_fundamentals", "aptitude", "quiz"])


def test_readiness_history_accumulates_snapshots(client, registered_user):
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 50},
                headers=registered_user["headers"])
    client.post("/api/v1/readiness/compute", headers=registered_user["headers"])
    client.post("/api/v1/readiness/compute", headers=registered_user["headers"])

    history_res = client.get("/api/v1/readiness/history", headers=registered_user["headers"])
    assert history_res.status_code == 200
    assert len(history_res.json()) == 2  # two separate snapshots, not overwritten


def test_tpo_dashboard_requires_admin_or_tpo_role(client, registered_user):
    res = client.get("/api/v1/tpo/dashboard", headers=registered_user["headers"])
    assert res.status_code == 403


def test_tpo_dashboard_flags_low_readiness_students(client, db_session, registered_user):
    from app.models.user import User

    # A single weak DSA quiz alone (weight 0.25) sits under the minimum data
    # coverage threshold for a published composite score - add a second
    # weak category so there's enough real signal to cross it.
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 20},
                headers=registered_user["headers"])
    client.post("/api/v1/quiz/submit", json={"subject": "Aptitude", "score_percent": 20},
                headers=registered_user["headers"])
    client.post("/api/v1/readiness/compute", headers=registered_user["headers"])

    # A separate admin account - promoting registered_user itself would
    # remove them from the dashboard's student list (it filters role='student')
    client.post("/api/v1/auth/register", json={
        "name": "TPO Admin", "email": "tpo@example.com", "password": "adminpass123",
    })
    admin = db_session.query(User).filter(User.email == "tpo@example.com").first()
    admin.role = "admin"
    db_session.commit()
    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "tpo@example.com", "password": "adminpass123",
    })
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = client.get("/api/v1/tpo/dashboard", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    flagged_emails = [s["email"] for s in body["flagged_students"]]
    assert registered_user["email"] in flagged_emails
