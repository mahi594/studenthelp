def test_non_admin_cannot_create_admin(client, registered_user):
    res = client.post("/api/v1/admin/create-admin", json={
        "name": "New Admin", "email": "newadmin1@example.com", "role": "admin",
    }, headers=registered_user["headers"])
    assert res.status_code == 403


def test_admin_can_create_admin_with_temp_password(client, admin_user):
    res = client.post("/api/v1/admin/create-admin", json={
        "name": "New Admin", "email": "newadmin2@example.com", "role": "admin",
    }, headers=admin_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "newadmin2@example.com"
    assert body["role"] == "admin"
    assert len(body["temp_password"]) >= 8
    # SMTP is mocked as unconfigured in tests (see mock_email fixture)
    assert body["email_sent"] is False


def test_tpo_admin_creation_requires_college_name(client, admin_user):
    res = client.post("/api/v1/admin/create-admin", json={
        "name": "TPO Person", "email": "tpo1@example.com", "role": "tpo_admin",
    }, headers=admin_user["headers"])
    assert res.status_code == 400


def test_cannot_create_admin_with_duplicate_email(client, admin_user, registered_user):
    res = client.post("/api/v1/admin/create-admin", json={
        "name": "Dup", "email": registered_user["email"], "role": "admin",
    }, headers=admin_user["headers"])
    assert res.status_code == 400


def test_new_admin_login_returns_restricted_token(client, admin_user):
    create_res = client.post("/api/v1/admin/create-admin", json={
        "name": "New Admin", "email": "newadmin3@example.com", "role": "admin",
    }, headers=admin_user["headers"])
    temp_password = create_res.json()["temp_password"]

    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "newadmin3@example.com", "password": temp_password,
    })
    assert login_res.status_code == 200
    body = login_res.json()
    assert body["must_change_password"] is True

    # The restricted token must not work for a normal protected endpoint.
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me_res.status_code == 401


def test_new_admin_must_change_password_before_full_access(client, admin_user):
    create_res = client.post("/api/v1/admin/create-admin", json={
        "name": "New Admin", "email": "newadmin4@example.com", "role": "admin",
    }, headers=admin_user["headers"])
    temp_password = create_res.json()["temp_password"]

    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "newadmin4@example.com", "password": temp_password,
    })
    restricted_token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/v1/auth/change-password",
        json={"new_password": "brandNewPass123"},
        headers={"Authorization": f"Bearer {restricted_token}"},
    )
    assert change_res.status_code == 200
    full_token = change_res.json()["access_token"]

    # Full access token now works normally.
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {full_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["must_change_password"] is False

    # And logging in again with the new password gives a normal (non-restricted) token.
    relogin_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "newadmin4@example.com", "password": "brandNewPass123",
    })
    assert relogin_res.status_code == 200
    assert relogin_res.json()["must_change_password"] is False


def test_change_password_rejects_short_password(client, admin_user):
    create_res = client.post("/api/v1/admin/create-admin", json={
        "name": "New Admin", "email": "newadmin5@example.com", "role": "admin",
    }, headers=admin_user["headers"])
    temp_password = create_res.json()["temp_password"]

    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "newadmin5@example.com", "password": temp_password,
    })
    restricted_token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/v1/auth/change-password",
        json={"new_password": "short"},
        headers={"Authorization": f"Bearer {restricted_token}"},
    )
    assert change_res.status_code == 400
