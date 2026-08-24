def test_ask_chat_question_and_get_answer(client, registered_user):
    res = client.post("/api/v1/chat/ask", json={"message": "How do I prepare for DSA rounds?"},
                       headers=registered_user["headers"])

    assert res.status_code == 200
    body = res.json()
    # Comes from the mocked answer_chat_question fixture in conftest.py
    assert body["answer"] == "Here's a general study tip."
    assert len(body["history"]) == 2  # user turn + assistant turn
    assert body["history"][0]["role"] == "user"
    assert body["history"][1]["role"] == "assistant"


def test_chat_with_invalid_company_id_returns_404(client, registered_user):
    res = client.post("/api/v1/chat/ask", json={
        "message": "What rounds does this company have?",
        "company_id": "00000000-0000-0000-0000-000000000000",
    }, headers=registered_user["headers"])
    assert res.status_code == 404


def test_chat_history_accumulates_across_turns(client, registered_user):
    client.post("/api/v1/chat/ask", json={"message": "First question"}, headers=registered_user["headers"])
    client.post("/api/v1/chat/ask", json={"message": "Second question"}, headers=registered_user["headers"])

    res = client.get("/api/v1/chat/history", headers=registered_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 4  # 2 user turns + 2 assistant turns
    contents = [m["content"] for m in body]
    assert "First question" in contents
    assert "Second question" in contents


def test_chat_history_is_scoped_per_user(client, registered_user):
    client.post("/api/v1/chat/ask", json={"message": "Only mine"}, headers=registered_user["headers"])

    client.post("/api/v1/auth/register", json={
        "name": "Other Chatter", "email": "other-chatter@example.com", "password": "otherpass123",
    })
    other_login = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "other-chatter@example.com", "password": "otherpass123",
    })
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    res = client.get("/api/v1/chat/history", headers=other_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_unauthenticated_user_cannot_chat(client):
    res = client.post("/api/v1/chat/ask", json={"message": "Hello"})
    assert res.status_code == 401
