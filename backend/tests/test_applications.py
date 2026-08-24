def _make_company(client, admin_user, name="Applications Test Corp"):
    res = client.post("/api/v1/companies/", json={"name": name, "roles": ["SDE-1"]},
                       headers=admin_user["headers"])
    return res.json()["id"]


def test_mark_application_creates_new_record(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)

    res = client.post("/api/v1/applications/mark", json={
        "company_id": company_id, "status": "applied",
    }, headers=registered_user["headers"])

    assert res.status_code == 200
    body = res.json()
    assert body["company_id"] == company_id
    assert body["status"] == "applied"
    assert body["applied_at"] is not None


def test_mark_application_upserts_existing_record(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)

    first = client.post("/api/v1/applications/mark", json={
        "company_id": company_id, "status": "applied",
    }, headers=registered_user["headers"]).json()

    second = client.post("/api/v1/applications/mark", json={
        "company_id": company_id, "status": "interviewing",
    }, headers=registered_user["headers"]).json()

    # Same row updated in place, not a duplicate
    assert second["id"] == first["id"]
    assert second["status"] == "interviewing"

    list_res = client.get("/api/v1/applications/", headers=registered_user["headers"])
    assert len(list_res.json()) == 1


def test_mark_application_requires_valid_company(client, registered_user):
    res = client.post("/api/v1/applications/mark", json={
        "company_id": "00000000-0000-0000-0000-000000000000", "status": "applied",
    }, headers=registered_user["headers"])
    assert res.status_code == 404


def test_list_applications_is_scoped_per_user(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)
    client.post("/api/v1/applications/mark", json={"company_id": company_id, "status": "applied"},
                headers=registered_user["headers"])

    client.post("/api/v1/auth/register", json={
        "name": "Other Applicant", "email": "other-applicant@example.com", "password": "otherpass123",
    })
    other_login = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "other-applicant@example.com", "password": "otherpass123",
    })
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    res = client.get("/api/v1/applications/", headers=other_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_unauthenticated_user_cannot_mark_application(client, admin_user):
    company_id = _make_company(client, admin_user)
    res = client.post("/api/v1/applications/mark", json={"company_id": company_id, "status": "applied"})
    assert res.status_code == 401
