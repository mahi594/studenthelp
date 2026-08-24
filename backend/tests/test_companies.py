def test_non_admin_cannot_create_company(client, registered_user):
    res = client.post("/api/v1/companies/", json={"name": "Test Corp"}, headers=registered_user["headers"])
    assert res.status_code == 403


def test_admin_can_create_company(client, admin_user):
    res = client.post("/api/v1/companies/", json={
        "name": "Test Corp",
        "roles": ["SDE-1"],
        "min_cgpa": "7.0",
        "preferred_branches": ["CSE"],
        "resume_keywords": ["DSA", "SQL"],
        "apply_url": "https://testcorp.example.com/careers",
    }, headers=admin_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Test Corp"
    assert body["apply_url"] == "https://testcorp.example.com/careers"


def test_list_and_search_companies(client, admin_user):
    client.post("/api/v1/companies/", json={"name": "Alpha Systems"}, headers=admin_user["headers"])
    client.post("/api/v1/companies/", json={"name": "Beta Labs"}, headers=admin_user["headers"])

    all_res = client.get("/api/v1/companies/")
    assert all_res.status_code == 200
    names = [c["name"] for c in all_res.json()]
    assert "Alpha Systems" in names
    assert "Beta Labs" in names

    search_res = client.get("/api/v1/companies/", params={"name": "Alpha"})
    search_names = [c["name"] for c in search_res.json()]
    assert "Alpha Systems" in search_names
    assert "Beta Labs" not in search_names


def test_unauthenticated_user_cannot_create_company(client):
    res = client.post("/api/v1/companies/", json={"name": "No Auth Corp"})
    assert res.status_code == 401


def test_admin_can_add_round_to_company(client, admin_user):
    company = client.post("/api/v1/companies/", json={"name": "Round Test Corp"},
                           headers=admin_user["headers"]).json()

    res = client.post(f"/api/v1/companies/{company['id']}/rounds", json={
        "order_index": 1,
        "round_type": "OA",
        "subjects_tested": ["DSA", "Aptitude"],
        "difficulty": "Medium",
        "notes": "90 minutes, 2 questions",
    }, headers=admin_user["headers"])

    assert res.status_code == 200
    body = res.json()
    assert len(body["rounds"]) == 1
    assert body["rounds"][0]["round_type"] == "OA"
    assert body["rounds"][0]["subjects_tested"] == ["DSA", "Aptitude"]


def test_non_admin_cannot_add_round(client, admin_user):
    company = client.post("/api/v1/companies/", json={"name": "Round Auth Corp"},
                           headers=admin_user["headers"]).json()

    # admin_user promotes the registered_user fixture in place, so a
    # separate student account is needed here to test non-admin access.
    client.post("/api/v1/auth/register", json={
        "name": "Non Admin", "email": "non-admin-rounds@example.com", "password": "studentpass123",
    })
    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "non-admin-rounds@example.com", "password": "studentpass123",
    })
    student_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = client.post(f"/api/v1/companies/{company['id']}/rounds", json={
        "order_index": 1, "round_type": "OA",
    }, headers=student_headers)
    assert res.status_code == 403


def test_add_round_requires_valid_company(client, admin_user):
    res = client.post("/api/v1/companies/00000000-0000-0000-0000-000000000000/rounds", json={
        "order_index": 1, "round_type": "OA",
    }, headers=admin_user["headers"])
    assert res.status_code == 404


def test_admin_can_delete_round(client, admin_user):
    company = client.post("/api/v1/companies/", json={"name": "Round Delete Corp"},
                           headers=admin_user["headers"]).json()
    with_round = client.post(f"/api/v1/companies/{company['id']}/rounds", json={
        "order_index": 1, "round_type": "HR",
    }, headers=admin_user["headers"]).json()
    round_id = with_round["rounds"][0]["id"]

    res = client.delete(f"/api/v1/companies/{company['id']}/rounds/{round_id}",
                         headers=admin_user["headers"])
    assert res.status_code == 200
    assert res.json()["rounds"] == []
