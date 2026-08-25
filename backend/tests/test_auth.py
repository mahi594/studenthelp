def test_register_and_login(client):
    res = client.post("/api/v1/auth/register", json={
        "name": "Jane Doe", "email": "jane@example.com", "password": "secret123",
        "branch": "CSE", "grad_year": 2027,
    })
    assert res.status_code == 200
    assert res.json()["email"] == "jane@example.com"

    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "jane@example.com", "password": "secret123",
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_register_with_institution_code(client):
    res = client.post("/api/v1/auth/register", json={
        "name": "Code Student", "email": "codestudent@example.com", "password": "secret123",
        "institution_code": "INST2026",
    })
    assert res.status_code == 200
    assert res.json()["college_name"] is not None



def test_login_wrong_password_fails(client):
    client.post("/api/v1/auth/register", json={
        "name": "Jane Doe", "email": "jane2@example.com", "password": "secret123",
    })
    res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "jane2@example.com", "password": "wrongpass",
    })
    assert res.status_code == 401


def test_duplicate_email_registration_fails(client):
    payload = {"name": "Dup", "email": "dup@example.com", "password": "secret123"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400


def test_protected_endpoint_requires_token(client):
    res = client.get("/api/v1/readiness/latest")
    assert res.status_code == 401


def test_forgot_password_dev_mode_returns_token(client, registered_user):
    """With no SMTP configured (the test default), forgot-password should
    return a dev_reset_token directly instead of silently failing."""
    res = client.post("/api/v1/auth/forgot-password", json={"email": registered_user["email"]})
    assert res.status_code == 200
    body = res.json()
    assert body.get("dev_reset_token") is not None


def test_forgot_password_unknown_email_does_not_leak(client):
    """Should return the same generic message whether or not the email exists."""
    res = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert res.status_code == 200
    assert res.json().get("dev_reset_token") is None


def test_reset_password_with_valid_token(client, registered_user):
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": registered_user["email"]})
    token = forgot_res.json()["dev_reset_token"]

    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": token, "new_password": "newpassword456",
    })
    assert reset_res.status_code == 200

    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": registered_user["email"], "password": "newpassword456",
    })
    assert login_res.status_code == 200


def test_reset_password_with_invalid_token_fails(client):
    res = client.post("/api/v1/auth/reset-password", json={
        "token": "not-a-real-token", "new_password": "whatever123",
    })
    assert res.status_code == 400


def test_me_returns_current_user_profile(client, registered_user):
    res = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == registered_user["email"]
    assert body["role"] == "student"


def test_me_requires_authentication(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
