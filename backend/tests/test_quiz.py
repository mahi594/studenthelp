import uuid


def unique_subject(base: str) -> str:
    """Quiz questions are stored globally by subject (not per-test), and the
    test DB persists across the whole session - a fixed subject like "DSA"
    would leak state between test functions. Suffix each test's subject to
    keep it isolated."""
    return f"{base}-{uuid.uuid4().hex[:8]}"


def test_manual_quiz_submit(client, registered_user):
    res = client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 65},
                       headers=registered_user["headers"])
    assert res.status_code == 200


def test_student_sees_no_questions_before_approval(client, admin_user, registered_user):
    """AI-generated questions default to pending_approval - students should
    not be able to fetch them until an admin approves."""
    subject = unique_subject("DSA")
    gen_res = client.post("/api/v1/admin/quiz/generate", json={
        "subject": subject, "num_questions": 1,
    }, headers=admin_user["headers"])
    assert gen_res.status_code == 200
    assert gen_res.json()[0]["status"] == "pending_approval"

    student_res = client.get("/api/v1/quiz/questions", params={"subject": subject},
                              headers=registered_user["headers"])
    assert student_res.status_code == 404


def test_full_quiz_generate_approve_take_flow(client, admin_user, registered_user):
    subject = unique_subject("DSA")
    gen_res = client.post("/api/v1/admin/quiz/generate", json={
        "subject": subject, "num_questions": 1,
    }, headers=admin_user["headers"])
    question = gen_res.json()[0]

    approve_res = client.post(f"/api/v1/admin/quiz/{question['id']}/approve", headers=admin_user["headers"])
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    fetch_res = client.get("/api/v1/quiz/questions", params={"subject": subject},
                            headers=registered_user["headers"])
    assert fetch_res.status_code == 200
    fetched_questions = fetch_res.json()
    assert len(fetched_questions) == 1
    # correct_option_index must never be exposed to students
    assert "correct_option_index" not in fetched_questions[0]

    submit_res = client.post("/api/v1/quiz/submit-answers", json={
        "subject": subject,
        "answers": [{"question_id": fetched_questions[0]["id"], "selected_option_index": 1}],
    }, headers=registered_user["headers"])
    assert submit_res.status_code == 200
    result = submit_res.json()
    assert result["score_percent"] == 100  # mocked correct answer is index 1
    assert result["correct_count"] == 1


def test_rejected_question_never_reaches_students(client, admin_user, registered_user):
    subject = unique_subject("OS")
    gen_res = client.post("/api/v1/admin/quiz/generate", json={
        "subject": subject, "num_questions": 1,
    }, headers=admin_user["headers"])
    question = gen_res.json()[0]

    client.post(f"/api/v1/admin/quiz/{question['id']}/reject", headers=admin_user["headers"])

    student_res = client.get("/api/v1/quiz/questions", params={"subject": subject},
                              headers=registered_user["headers"])
    assert student_res.status_code == 404
