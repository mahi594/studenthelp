def _register_and_login(client, email, name="Other User"):
    client.post("/api/v1/auth/register", json={"name": name, "email": email, "password": "testpass123"})
    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": email, "password": "testpass123",
    })
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


def test_post_and_list_questions(client, registered_user):
    res = client.post("/api/v1/qa/questions", json={
        "title": "Anyone interviewed at Amazon recently?",
        "body": "Curious what the OA looks like this year.",
        "tags": ["Amazon", "OA"],
    }, headers=registered_user["headers"])
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Anyone interviewed at Amazon recently?"
    assert body["answers"] == []

    list_res = client.get("/api/v1/qa/questions")
    assert list_res.status_code == 200
    matching = [q for q in list_res.json() if q["id"] == body["id"]]
    assert len(matching) == 1
    assert matching[0]["answer_count"] == 0


def test_question_requires_authentication(client):
    res = client.post("/api/v1/qa/questions", json={"title": "T", "body": "B"})
    assert res.status_code == 401


def test_question_with_invalid_company_fails(client, registered_user):
    res = client.post("/api/v1/qa/questions", json={
        "title": "T", "body": "B", "company_id": "00000000-0000-0000-0000-000000000000",
    }, headers=registered_user["headers"])
    assert res.status_code == 404


def test_answer_a_question(client, registered_user):
    q = client.post("/api/v1/qa/questions", json={"title": "T", "body": "B"},
                     headers=registered_user["headers"]).json()

    other_headers = _register_and_login(client, "qa-answerer@example.com")
    res = client.post(f"/api/v1/qa/questions/{q['id']}/answers", json={"body": "Here's my answer."},
                       headers=other_headers)
    assert res.status_code == 200
    assert res.json()["upvotes"] == 0

    detail_res = client.get(f"/api/v1/qa/questions/{q['id']}")
    assert len(detail_res.json()["answers"]) == 1
    assert detail_res.json()["answers"][0]["author_name"] == "Other User"


def test_upvote_answer(client, registered_user):
    q = client.post("/api/v1/qa/questions", json={"title": "T", "body": "B"},
                     headers=registered_user["headers"]).json()
    other_headers = _register_and_login(client, "qa-upvoter@example.com")
    answer = client.post(f"/api/v1/qa/questions/{q['id']}/answers", json={"body": "A"},
                          headers=other_headers).json()

    res = client.post(f"/api/v1/qa/answers/{answer['id']}/upvote", headers=registered_user["headers"])
    assert res.status_code == 200
    assert res.json()["upvotes"] == 1


def test_filter_questions_by_company(client, registered_user, admin_user):
    company = client.post("/api/v1/companies/", json={"name": "QA Filter Corp"},
                           headers=admin_user["headers"]).json()

    client.post("/api/v1/qa/questions", json={"title": "General question", "body": "B"},
                headers=registered_user["headers"])
    client.post("/api/v1/qa/questions", json={"title": "Company-specific", "body": "B", "company_id": company["id"]},
                headers=registered_user["headers"])

    res = client.get(f"/api/v1/qa/questions?company_id={company['id']}")
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "Company-specific"


def test_admin_can_hide_question(client, registered_user, admin_user):
    q = client.post("/api/v1/qa/questions", json={"title": "To be hidden", "body": "B"},
                     headers=registered_user["headers"]).json()

    hide_res = client.delete(f"/api/v1/qa/questions/{q['id']}", headers=admin_user["headers"])
    assert hide_res.status_code == 200

    list_res = client.get("/api/v1/qa/questions")
    assert q["id"] not in [item["id"] for item in list_res.json()]

    detail_res = client.get(f"/api/v1/qa/questions/{q['id']}")
    assert detail_res.status_code == 404


def test_non_admin_cannot_hide_question(client, registered_user):
    q = client.post("/api/v1/qa/questions", json={"title": "T", "body": "B"},
                     headers=registered_user["headers"]).json()
    res = client.delete(f"/api/v1/qa/questions/{q['id']}", headers=registered_user["headers"])
    assert res.status_code == 403


def test_get_nonexistent_question_404s(client):
    res = client.get("/api/v1/qa/questions/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404
