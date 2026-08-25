def test_mock_interview_full_flow(client, registered_user):
    start_res = client.post("/api/v1/mock-interview/start", json={
        "role_or_subject": "SDE-1",
    }, headers=registered_user["headers"])
    assert start_res.status_code == 200
    session = start_res.json()
    assert session["status"] == "in_progress"
    assert len(session["transcript"]) == 1
    assert session["transcript"][0]["role"] == "interviewer"

    respond_res = client.post(f"/api/v1/mock-interview/{session['id']}/respond", json={
        "answer": "I led a team project building a REST API for our final year submission.",
    }, headers=registered_user["headers"])
    assert respond_res.status_code == 200
    assert len(respond_res.json()["transcript"]) == 3  # opening Q, candidate answer, follow-up Q

    finish_res = client.post(f"/api/v1/mock-interview/{session['id']}/finish", headers=registered_user["headers"])
    assert finish_res.status_code == 200
    finished = finish_res.json()
    assert finished["status"] == "completed"
    assert finished["overall_score"] == 68  # from the mocked score_mock_interview
    assert "strengths" in finished["feedback"]


def test_cannot_respond_to_completed_session(client, registered_user):
    start_res = client.post("/api/v1/mock-interview/start", json={
        "role_or_subject": "SDE-1",
    }, headers=registered_user["headers"])
    session_id = start_res.json()["id"]
    client.post(f"/api/v1/mock-interview/{session_id}/finish", headers=registered_user["headers"])

    res = client.post(f"/api/v1/mock-interview/{session_id}/respond", json={
        "answer": "too late",
    }, headers=registered_user["headers"])
    assert res.status_code == 400


def test_completed_mock_interview_feeds_readiness_score(client, registered_user):
    """A single mock interview (weight 0.10) is real signal but, alone, is
    below the minimum data-coverage threshold for a published composite
    score - it should show up as the interview dimension with no fabricated
    overall number."""
    start_res = client.post("/api/v1/mock-interview/start", json={
        "role_or_subject": "SDE-1",
    }, headers=registered_user["headers"])
    session_id = start_res.json()["id"]
    client.post(f"/api/v1/mock-interview/{session_id}/finish", headers=registered_user["headers"])

    readiness_res = client.get("/api/v1/readiness/latest", headers=registered_user["headers"])
    assert readiness_res.status_code == 200
    body = readiness_res.json()
    assert body["composite_score"] is None
    assert body["data_status"] == "insufficient"
    assert body["breakdown"]["interview"] == 68
    assert "interview" in body["breakdown"]["components_used"]


def test_cannot_access_another_users_session(client, registered_user):
    start_res = client.post("/api/v1/mock-interview/start", json={
        "role_or_subject": "SDE-1",
    }, headers=registered_user["headers"])
    session_id = start_res.json()["id"]

    # A completely different (unauthenticated) request shouldn't be able to read it
    res = client.get(f"/api/v1/mock-interview/{session_id}")
    assert res.status_code == 401


def test_mock_interview_structured_dimensions_and_readiness_integration(client, registered_user):
    start_res = client.post("/api/v1/mock-interview/start", json={
        "role_or_subject": "SDE-1",
    }, headers=registered_user["headers"])
    session_id = start_res.json()["id"]

    finish_res = client.post(f"/api/v1/mock-interview/{session_id}/finish", headers=registered_user["headers"])
    assert finish_res.status_code == 200
    fb = finish_res.json()["feedback"]
    assert "technical_knowledge" in fb
    assert "problem_solving" in fb
    assert "communication_score" in fb
    assert "answer_structure" in fb
    assert "technical_depth" in fb

    readiness_res = client.get("/api/v1/readiness/latest", headers=registered_user["headers"])
    assert readiness_res.status_code == 200
    bd = readiness_res.json()["breakdown"]
    assert bd["communication"] is not None

