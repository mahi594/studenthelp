def _make_company(client, admin_user, name="Prep Test Corp"):
    res = client.post("/api/v1/companies/", json={
        "name": name,
        "roles": ["SDE-1"],
        "preferred_branches": ["CSE"],
        "resume_keywords": ["DSA"],
    }, headers=admin_user["headers"])
    return res.json()["id"]


def test_prep_plan_requires_quiz_results_first(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)

    res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 14,
    }, headers=registered_user["headers"])

    assert res.status_code == 400
    assert "quiz" in res.json()["detail"].lower()


def test_prep_plan_requires_valid_company(client, registered_user):
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 40},
                headers=registered_user["headers"])

    res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": "00000000-0000-0000-0000-000000000000",
        "days_total": 14,
    }, headers=registered_user["headers"])

    assert res.status_code == 404


def test_generate_and_fetch_prep_plan(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 40},
                headers=registered_user["headers"])

    gen_res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 14,
    }, headers=registered_user["headers"])

    assert gen_res.status_code == 200
    body = gen_res.json()
    assert body["target_company_id"] == company_id
    assert body["days_total"] == 14
    assert body["progress_percent"] == 0
    # Comes from the mocked generate_prep_plan fixture in conftest.py
    assert body["tasks"][0]["topic"] == "DSA"

    fetch_res = client.get(f"/api/v1/prep-plan/{body['id']}", headers=registered_user["headers"])
    assert fetch_res.status_code == 200
    assert fetch_res.json()["id"] == body["id"]


def test_fetch_prep_plan_requires_authentication(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 40},
                headers=registered_user["headers"])
    gen_res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 14,
    }, headers=registered_user["headers"])
    plan_id = gen_res.json()["id"]

    res = client.get(f"/api/v1/prep-plan/{plan_id}")
    assert res.status_code == 401


def test_cannot_fetch_someone_elses_prep_plan(client, registered_user, admin_user):
    import uuid
    company_id = _make_company(client, admin_user)
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 40},
                headers=registered_user["headers"])
    gen_res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 14,
    }, headers=registered_user["headers"])
    plan_id = gen_res.json()["id"]

    other_email = f"other-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={"name": "Other", "email": other_email, "password": "testpass123"})
    other_login = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": other_email, "password": "testpass123",
    })
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    res = client.get(f"/api/v1/prep-plan/{plan_id}", headers=other_headers)
    assert res.status_code == 403


def test_latest_prep_plan_404_when_none_generated(client, registered_user):
    res = client.get("/api/v1/prep-plan/latest", headers=registered_user["headers"])
    assert res.status_code == 404


def test_latest_prep_plan_returns_most_recent(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user, name="Latest Plan Corp")
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 40},
                headers=registered_user["headers"])
    gen_res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 7,
    }, headers=registered_user["headers"])

    res = client.get("/api/v1/prep-plan/latest", headers=registered_user["headers"])
    assert res.status_code == 200
    assert res.json()["id"] == gen_res.json()["id"]


def test_unauthenticated_user_cannot_generate_prep_plan(client, admin_user):
    company_id = _make_company(client, admin_user)
    res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 14,
    })
    assert res.status_code == 401


def test_update_prep_plan_task_status_and_recalculate_progress(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user, name="Task Update Corp")
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 50},
                headers=registered_user["headers"])
    gen_res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 14,
    }, headers=registered_user["headers"])
    assert gen_res.status_code == 200
    plan_id = gen_res.json()["id"]
    tasks = gen_res.json()["tasks"]
    assert len(tasks) > 0

    # Mark first task as completed
    patch_res = client.patch(f"/api/v1/prep-plan/{plan_id}/tasks/0", json={"completed": True},
                             headers=registered_user["headers"])
    assert patch_res.status_code == 200
    updated_plan = patch_res.json()
    assert updated_plan["tasks"][0]["completed"] is True
    assert updated_plan["tasks"][0]["status"] == "completed"
    expected_progress = round((1 / len(tasks)) * 100)
    assert updated_plan["progress_percent"] == expected_progress


def test_cannot_update_other_users_prep_plan_task(client, registered_user, admin_user):
    import uuid
    company_id = _make_company(client, admin_user, name="Other User Task Corp")
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 50},
                headers=registered_user["headers"])
    gen_res = client.post("/api/v1/prep-plan/generate", json={
        "target_company_id": company_id,
        "days_total": 14,
    }, headers=registered_user["headers"])
    plan_id = gen_res.json()["id"]

    other_email = f"other2-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={"name": "Other2", "email": other_email, "password": "testpass123"})
    other_login = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": other_email, "password": "testpass123",
    })
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    res = client.patch(f"/api/v1/prep-plan/{plan_id}/tasks/0", json={"completed": True}, headers=other_headers)
    assert res.status_code == 403

