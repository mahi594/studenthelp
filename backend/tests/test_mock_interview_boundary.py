import pytest
import uuid
from unittest.mock import patch
from app.models.user import User
from app.models.institution import Institution
from app.models.mock_interview import MockInterviewSession
from app.api.v1.endpoints.mock_interview import validate_mock_interview_scores
from app.api.v1.endpoints.auth import hash_password

def test_mock_interview_score_validation_boundary():
    valid = {
        "overall_score": 85,
        "technical_knowledge": 80,
        "problem_solving": 90,
        "communication_score": 85,
        "answer_structure": 80,
        "technical_depth": 85,
    }
    assert validate_mock_interview_scores(valid)["overall_score"] == 85

    with pytest.raises(ValueError, match="overall_score"):
        validate_mock_interview_scores({"technical_knowledge": 80, "problem_solving": 90, "communication_score": 85, "answer_structure": 80, "technical_depth": 85})

    with pytest.raises(ValueError, match="technical_knowledge"):
        validate_mock_interview_scores({"overall_score": 85, "problem_solving": 90, "communication_score": 85, "answer_structure": 80, "technical_depth": 85})

    with pytest.raises(ValueError, match="problem_solving"):
        validate_mock_interview_scores({"overall_score": 85, "technical_knowledge": 80, "communication_score": 85, "answer_structure": 80, "technical_depth": 85})

    with pytest.raises(ValueError, match="communication_score"):
        validate_mock_interview_scores({"overall_score": 85, "technical_knowledge": 80, "problem_solving": 90, "answer_structure": 80, "technical_depth": 85})

    with pytest.raises(ValueError, match="answer_structure"):
        validate_mock_interview_scores({"overall_score": 85, "technical_knowledge": 80, "problem_solving": 90, "communication_score": 85, "technical_depth": 85})

    with pytest.raises(ValueError, match="technical_depth"):
        validate_mock_interview_scores({"overall_score": 85, "technical_knowledge": 80, "problem_solving": 90, "communication_score": 85, "answer_structure": 80})

    with pytest.raises(ValueError, match="outside allowed 0-100 range"):
        validate_mock_interview_scores({**valid, "overall_score": -5})

    with pytest.raises(ValueError, match="outside allowed 0-100 range"):
        validate_mock_interview_scores({**valid, "overall_score": 105})

    with pytest.raises(ValueError, match="not a valid number"):
        validate_mock_interview_scores({**valid, "overall_score": "eighty-five"})

    with pytest.raises(ValueError, match="not a valid JSON object"):
        validate_mock_interview_scores("Not JSON")

def test_finish_mock_interview_endpoint_rejection(client, db_session):
    inst = Institution(name="Mock Tech", code="MOCK2026")
    db_session.add(inst)
    db_session.commit()

    pwd = hash_password("password123")

    student = User(name="Mock Candidate", email="candidate@mock.edu", hashed_password=pwd, role="student", institution_id=inst.id)
    db_session.add(student)
    db_session.commit()

    session = MockInterviewSession(
        user_id=student.id,
        role_or_subject="Software Engineer",
        status="in_progress",
        transcript=[{"role": "interviewer", "content": "Tell me about yourself."}],
    )
    db_session.add(session)
    db_session.commit()

    token = client.post("/api/v1/auth/login", data={"username": student.email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.api.v1.endpoints.mock_interview.score_mock_interview", side_effect=Exception("AI Service Error")):
        res = client.post(f"/api/v1/mock-interview/{session.id}/finish", headers=headers)
        assert res.status_code == 502
        assert res.json()["detail"] == "The interview evaluation could not be completed. Please try again."

    db_session.refresh(session)
    assert session.status == "in_progress"
    assert session.overall_score is None


def test_finish_mock_interview_endpoint_all_failure_modes(client, db_session):
    inst = Institution(name="Mock Tech Failure Test", code="MOCKFAIL2026")
    db_session.add(inst)
    db_session.commit()

    pwd = hash_password("password123")
    student = User(name="Failure Test Student", email="failtest@mock.edu", hashed_password=pwd, role="student", institution_id=inst.id)
    db_session.add(student)
    db_session.commit()

    valid_dict = {
        "overall_score": 85,
        "technical_knowledge": 80,
        "problem_solving": 90,
        "communication_score": 85,
        "answer_structure": 80,
        "technical_depth": 85,
        "strengths": ["Good DSA"],
        "improvements": ["More depth"],
    }

    invalid_payloads = [
        ("missing overall_score", {k: v for k, v in valid_dict.items() if k != "overall_score"}),
        ("missing technical_knowledge", {k: v for k, v in valid_dict.items() if k != "technical_knowledge"}),
        ("missing problem_solving", {k: v for k, v in valid_dict.items() if k != "problem_solving"}),
        ("missing communication_score", {k: v for k, v in valid_dict.items() if k != "communication_score"}),
        ("missing answer_structure", {k: v for k, v in valid_dict.items() if k != "answer_structure"}),
        ("missing technical_depth", {k: v for k, v in valid_dict.items() if k != "technical_depth"}),
        ("score below 0", {**valid_dict, "overall_score": -10}),
        ("score above 100", {**valid_dict, "overall_score": 150}),
        ("non-numeric score", {**valid_dict, "overall_score": "invalid_score"}),
    ]

    token = client.post("/api/v1/auth/login", data={"username": student.email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test each invalid payload: rejected with HTTP 502 and session stays in_progress
    for label, payload in invalid_payloads:
        sess = MockInterviewSession(
            user_id=student.id,
            role_or_subject="Software Engineer",
            status="in_progress",
            transcript=[{"role": "interviewer", "content": "Question?"}],
        )
        db_session.add(sess)
        db_session.commit()

        with patch("app.api.v1.endpoints.mock_interview.score_mock_interview", return_value=payload):
            res = client.post(f"/api/v1/mock-interview/{sess.id}/finish", headers=headers)
            assert res.status_code == 502, f"Failed for {label}"

        db_session.refresh(sess)
        assert sess.status == "in_progress", f"Status changed for {label}"
        assert sess.overall_score is None, f"Score persisted for {label}"

    # Test malformed AI JSON, AI timeout, AI provider failure
    ai_errors = [
        ("malformed AI JSON", Exception("Invalid JSON returned by LLM")),
        ("AI timeout", TimeoutError("AI response timed out")),
        ("AI provider failure", RuntimeError("AI provider returned HTTP 500")),
    ]
    for label, exc in ai_errors:
        sess = MockInterviewSession(
            user_id=student.id,
            role_or_subject="Software Engineer",
            status="in_progress",
            transcript=[{"role": "interviewer", "content": "Question?"}],
        )
        db_session.add(sess)
        db_session.commit()

        with patch("app.api.v1.endpoints.mock_interview.score_mock_interview", side_effect=exc):
            res = client.post(f"/api/v1/mock-interview/{sess.id}/finish", headers=headers)
            assert res.status_code == 502, f"Failed for {label}"

        db_session.refresh(sess)
        assert sess.status == "in_progress", f"Status changed for {label}"
        assert sess.overall_score is None, f"Score persisted for {label}"

    # Test valid evaluation -> persisted correctly
    sess = MockInterviewSession(
        user_id=student.id,
        role_or_subject="Software Engineer",
        status="in_progress",
        transcript=[{"role": "interviewer", "content": "Question?"}],
    )
    db_session.add(sess)
    db_session.commit()

    with patch("app.api.v1.endpoints.mock_interview.score_mock_interview", return_value=valid_dict):
        res = client.post(f"/api/v1/mock-interview/{sess.id}/finish", headers=headers)
        assert res.status_code == 200

    db_session.refresh(sess)
    assert sess.status == "completed"
    assert sess.overall_score == 85

