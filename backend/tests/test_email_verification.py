from jose import jwt

from app.core.config import settings


def test_new_user_starts_unverified(client, registered_user):
    res = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert res.json()["email_verified"] is False


def test_resend_verification_returns_dev_token_without_smtp(client, registered_user):
    res = client.post("/api/v1/auth/resend-verification", headers=registered_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["dev_verify_token"] is not None


def test_verify_email_with_valid_token(client, registered_user):
    resend_res = client.post("/api/v1/auth/resend-verification", headers=registered_user["headers"])
    token = resend_res.json()["dev_verify_token"]

    verify_res = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify_res.status_code == 200

    me_res = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert me_res.json()["email_verified"] is True


def test_verify_email_with_invalid_token_fails(client):
    res = client.post("/api/v1/auth/verify-email", json={"token": "not-a-real-token"})
    assert res.status_code == 400


def test_verify_email_rejects_wrong_scope_token(client, registered_user):
    """A password-reset token shouldn't also work as a verification token -
    scope must be checked, not just signature validity."""
    reset_res = client.post("/api/v1/auth/forgot-password", json={"email": registered_user["email"]})
    reset_token = reset_res.json()["dev_reset_token"]

    res = client.post("/api/v1/auth/verify-email", json={"token": reset_token})
    assert res.status_code == 400


def test_resend_verification_requires_authentication(client):
    res = client.post("/api/v1/auth/resend-verification")
    assert res.status_code == 401


def test_already_verified_user_gets_friendly_message(client, registered_user):
    resend_res = client.post("/api/v1/auth/resend-verification", headers=registered_user["headers"])
    token = resend_res.json()["dev_verify_token"]
    client.post("/api/v1/auth/verify-email", json={"token": token})

    second_res = client.post("/api/v1/auth/resend-verification", headers=registered_user["headers"])
    assert "already verified" in second_res.json()["message"].lower()
