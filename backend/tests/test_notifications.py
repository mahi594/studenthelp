def _register_and_login(client, email, name="Other User"):
    client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "testpass123"})
    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": email, "password": "testpass123",
    })
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


def test_no_notifications_initially(client, registered_user):
    res = client.get("/api/v1/notifications/", headers=registered_user["headers"])
    assert res.status_code == 200
    assert res.json() == []

    count_res = client.get("/api/v1/notifications/unread-count", headers=registered_user["headers"])
    assert count_res.json()["count"] == 0


def test_answering_a_question_notifies_the_author(client, registered_user):
    question_res = client.post("/api/v1/qa/questions", json={
        "title": "How hard is the Google OA?",
        "body": "Wondering what to expect.",
    }, headers=registered_user["headers"])
    question_id = question_res.json()["id"]

    other_headers = _register_and_login(client, "answerer@example.com", "Answerer")
    client.post(f"/api/v1/qa/questions/{question_id}/answers", json={
        "body": "It's mostly DSA, 2 questions, 90 minutes.",
    }, headers=other_headers)

    res = client.get("/api/v1/notifications/", headers=registered_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["type"] == "qa_reply"
    assert body[0]["is_read"] is False

    count_res = client.get("/api/v1/notifications/unread-count", headers=registered_user["headers"])
    assert count_res.json()["count"] == 1


def test_answering_own_question_does_not_self_notify(client, registered_user):
    question_res = client.post("/api/v1/qa/questions", json={
        "title": "Self-answered question", "body": "...",
    }, headers=registered_user["headers"])
    question_id = question_res.json()["id"]

    client.post(f"/api/v1/qa/questions/{question_id}/answers", json={"body": "Answering myself."},
                headers=registered_user["headers"])

    res = client.get("/api/v1/notifications/", headers=registered_user["headers"])
    assert res.json() == []


def test_mark_notification_read(client, registered_user):
    question_res = client.post("/api/v1/qa/questions", json={"title": "Q", "body": "B"},
                                headers=registered_user["headers"])
    other_headers = _register_and_login(client, "answerer2@example.com")
    client.post(f"/api/v1/qa/questions/{question_res.json()['id']}/answers", json={"body": "A"},
                headers=other_headers)

    notif_id = client.get("/api/v1/notifications/", headers=registered_user["headers"]).json()[0]["id"]

    res = client.post(f"/api/v1/notifications/{notif_id}/read", headers=registered_user["headers"])
    assert res.status_code == 200
    assert res.json()["is_read"] is True

    count_res = client.get("/api/v1/notifications/unread-count", headers=registered_user["headers"])
    assert count_res.json()["count"] == 0


def test_cannot_mark_someone_elses_notification_read(client, registered_user):
    question_res = client.post("/api/v1/qa/questions", json={"title": "Q", "body": "B"},
                                headers=registered_user["headers"])
    other_headers = _register_and_login(client, "answerer3@example.com")
    client.post(f"/api/v1/qa/questions/{question_res.json()['id']}/answers", json={"body": "A"},
                headers=other_headers)
    notif_id = client.get("/api/v1/notifications/", headers=registered_user["headers"]).json()[0]["id"]

    res = client.post(f"/api/v1/notifications/{notif_id}/read", headers=other_headers)
    assert res.status_code == 404


def test_mark_all_read(client, registered_user):
    other_headers = _register_and_login(client, "answerer4@example.com")
    for i in range(3):
        q = client.post("/api/v1/qa/questions", json={"title": f"Q{i}", "body": "B"},
                         headers=registered_user["headers"]).json()
        client.post(f"/api/v1/qa/questions/{q['id']}/answers", json={"body": "A"}, headers=other_headers)

    client.post("/api/v1/notifications/read-all", headers=registered_user["headers"])
    count_res = client.get("/api/v1/notifications/unread-count", headers=registered_user["headers"])
    assert count_res.json()["count"] == 0


def test_notifications_require_authentication(client):
    res = client.get("/api/v1/notifications/")
    assert res.status_code == 401
