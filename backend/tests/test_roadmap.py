def test_roadmap_requires_quiz_results_first(client, registered_user):
    res = client.post("/api/v1/roadmap/generate", json={
        "horizon_months": 6,
        "target_company_ids": [],
    }, headers=registered_user["headers"])

    assert res.status_code == 400
    assert "quiz" in res.json()["detail"].lower()


def test_generate_roadmap_and_fetch_latest(client, registered_user):
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 35},
                headers=registered_user["headers"])

    gen_res = client.post("/api/v1/roadmap/generate", json={
        "horizon_months": 6,
        "target_company_ids": [],
    }, headers=registered_user["headers"])

    assert gen_res.status_code == 200
    body = gen_res.json()
    assert body["horizon_months"] == 6
    # Comes from the mocked generate_roadmap fixture in conftest.py
    assert body["phases"][0]["phase"] == "Month 1"

    latest_res = client.get("/api/v1/roadmap/user/latest", headers=registered_user["headers"])
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == body["id"]


def test_latest_roadmap_404_when_none_generated(client, registered_user):
    res = client.get("/api/v1/roadmap/user/latest", headers=registered_user["headers"])
    assert res.status_code == 404


def test_latest_roadmap_returns_most_recent(client, registered_user):
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 35},
                headers=registered_user["headers"])

    first = client.post("/api/v1/roadmap/generate", json={"horizon_months": 3, "target_company_ids": []},
                         headers=registered_user["headers"]).json()
    second = client.post("/api/v1/roadmap/generate", json={"horizon_months": 6, "target_company_ids": []},
                          headers=registered_user["headers"]).json()

    latest_res = client.get("/api/v1/roadmap/user/latest", headers=registered_user["headers"])
    assert latest_res.json()["id"] == second["id"]
    assert latest_res.json()["id"] != first["id"]


def test_unauthenticated_user_cannot_generate_roadmap(client):
    res = client.post("/api/v1/roadmap/generate", json={"horizon_months": 6, "target_company_ids": []})
    assert res.status_code == 401


def test_get_roadmap_by_id_requires_authentication(client, registered_user):
    """Previously GET /roadmap/{id} had no auth dependency at all - anyone
    could read any roadmap by guessing its UUID."""
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 35},
                headers=registered_user["headers"])
    gen_res = client.post("/api/v1/roadmap/generate", json={"horizon_months": 6, "target_company_ids": []},
                           headers=registered_user["headers"])
    roadmap_id = gen_res.json()["id"]

    res = client.get(f"/api/v1/roadmap/{roadmap_id}")
    assert res.status_code == 401


def test_get_roadmap_by_id_blocks_other_users(client, registered_user):
    """IDOR guard: a second student must not be able to fetch the first
    student's roadmap by ID."""
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 35},
                headers=registered_user["headers"])
    gen_res = client.post("/api/v1/roadmap/generate", json={"horizon_months": 6, "target_company_ids": []},
                           headers=registered_user["headers"])
    roadmap_id = gen_res.json()["id"]

    client.post("/api/v1/auth/register", json={
        "name": "Other Student", "email": "other-roadmap-viewer@example.com", "password": "otherpass123",
    })
    other_login = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "other-roadmap-viewer@example.com", "password": "otherpass123",
    })
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    res = client.get(f"/api/v1/roadmap/{roadmap_id}", headers=other_headers)
    assert res.status_code == 404

    own_res = client.get(f"/api/v1/roadmap/{roadmap_id}", headers=registered_user["headers"])
    assert own_res.status_code == 200
