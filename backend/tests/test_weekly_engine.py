import uuid

from app.services.weekly_engine_service import send_weekly_quiz_reminders, generate_weekly_prep_plans


def unique_subject(base: str) -> str:
    return f"{base}-{uuid.uuid4().hex[:8]}"


def _approved_question(client, admin_headers, subject: str, correct_index: int = 1):
    gen_res = client.post("/api/v1/admin/quiz/generate", json={
        "subject": subject, "num_questions": 1,
    }, headers=admin_headers)
    question = gen_res.json()[0]
    client.post(f"/api/v1/admin/quiz/{question['id']}/approve", headers=admin_headers)
    return question


def test_weekly_status_shows_all_subjects_as_due_when_never_taken(client, registered_user):
    res = client.get("/api/v1/quiz/weekly-status", headers=registered_user["headers"])
    assert res.status_code == 200
    statuses = res.json()
    assert len(statuses) == 6  # WEEKLY_QUIZ_SUBJECTS
    assert all(s["is_due"] for s in statuses)
    assert all(s["last_taken_at"] is None for s in statuses)


def test_weekly_status_reflects_recent_attempt_as_not_due(client, registered_user):
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 80},
                headers=registered_user["headers"])
    res = client.get("/api/v1/quiz/weekly-status", headers=registered_user["headers"])
    dsa_status = next(s for s in res.json() if s["subject"] == "DSA")
    assert dsa_status["is_due"] is False
    assert dsa_status["last_score_percent"] == 80
    assert dsa_status["next_eligible_at"] is not None


def test_weak_quiz_score_returns_leetcode_recommendations_and_notifies(client, admin_user, registered_user):
    subject = unique_subject("DSA")
    question = _approved_question(client, admin_user["headers"], subject)

    # The mocked generated question's correct_option_index is always 1 (see
    # conftest mock_ai) - answering 0 is deliberately wrong, forcing a low score.
    submit_res = client.post("/api/v1/quiz/submit-answers", json={
        "subject": subject,
        "answers": [{"question_id": question["id"], "selected_option_index": 0}],
    }, headers=registered_user["headers"])
    assert submit_res.status_code == 200
    body = submit_res.json()
    assert body["score_percent"] == 0
    assert body["is_weak_subject"] is True
    assert len(body["recommended_leetcode"]) > 0

    notif_res = client.get("/api/v1/notifications/", headers=registered_user["headers"])
    notif_types = [n["type"] for n in notif_res.json()]
    assert "leetcode_recommendation" in notif_types


def test_strong_quiz_score_does_not_recommend_or_notify(client, admin_user, registered_user):
    subject = unique_subject("DSA")
    question = _approved_question(client, admin_user["headers"], subject)

    # The mocked generated question's correct_option_index is always 1 (see conftest mock_ai).
    submit_res = client.post("/api/v1/quiz/submit-answers", json={
        "subject": subject,
        "answers": [{"question_id": question["id"], "selected_option_index": 1}],
    }, headers=registered_user["headers"])
    assert submit_res.status_code == 200
    body = submit_res.json()
    assert body["score_percent"] == 100
    assert body["is_weak_subject"] is False
    assert body["recommended_leetcode"] == []


def test_leetcode_recommendations_for_me_uses_latest_weak_attempt(client, admin_user, registered_user):
    subject = unique_subject("DBMS")
    question = _approved_question(client, admin_user["headers"], subject)

    client.post("/api/v1/quiz/submit-answers", json={
        "subject": subject,
        "answers": [{"question_id": question["id"], "selected_option_index": 0}],  # wrong -> 0%
    }, headers=registered_user["headers"])

    res = client.get("/api/v1/leetcode/recommendations/for-me", headers=registered_user["headers"])
    assert res.status_code == 200
    assert len(res.json()) > 0


def test_leetcode_recommendations_for_me_empty_with_no_weak_subjects(client, registered_user):
    res = client.get("/api/v1/leetcode/recommendations/for-me", headers=registered_user["headers"])
    assert res.status_code == 200
    assert res.json() == []


def test_send_weekly_quiz_reminders_notifies_students_with_due_subjects(client, registered_user, db_session):
    sent = send_weekly_quiz_reminders(db_session)
    assert sent >= 1

    notif_res = client.get("/api/v1/notifications/", headers=registered_user["headers"])
    notif_types = [n["type"] for n in notif_res.json()]
    assert "weekly_quiz_reminder" in notif_types


def test_send_weekly_quiz_reminders_does_not_double_send_same_week(client, registered_user, db_session):
    send_weekly_quiz_reminders(db_session)
    second_run_count = send_weekly_quiz_reminders(db_session)
    # Second run shouldn't re-notify the same student within the same week.
    notif_res = client.get("/api/v1/notifications/", headers=registered_user["headers"])
    reminder_count = len([n for n in notif_res.json() if n["type"] == "weekly_quiz_reminder"])
    assert reminder_count == 1


def test_generate_weekly_prep_plans_skips_students_without_target_company(db_session, registered_user):
    generated = generate_weekly_prep_plans(db_session)
    assert generated == 0  # registered_user has no target_company_ids and no quiz history
