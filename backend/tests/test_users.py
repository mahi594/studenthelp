def test_update_profile_partial_fields(client, registered_user):
    res = client.patch("/api/v1/users/me", json={"branch": "IT", "cgpa": "8.2"},
                        headers=registered_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["branch"] == "IT"
    assert body["cgpa"] == "8.2"
    # grad_year was set at registration (2027) and not touched by this PATCH
    assert body["grad_year"] == 2027


def test_update_profile_does_not_clear_omitted_fields(client, registered_user):
    client.patch("/api/v1/users/me", json={"college_name": "Test University"},
                 headers=registered_user["headers"])

    res = client.patch("/api/v1/users/me", json={"cgpa": "9.0"}, headers=registered_user["headers"])
    body = res.json()
    assert body["cgpa"] == "9.0"
    assert body["college_name"] == "Test University"  # untouched by the second PATCH


def test_update_profile_requires_authentication(client):
    res = client.patch("/api/v1/users/me", json={"branch": "IT"})
    assert res.status_code == 401
