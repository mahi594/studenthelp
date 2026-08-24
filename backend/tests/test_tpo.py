"""
Tenant isolation + IDOR tests for /tpo/* endpoints, plus tests proving
intervention improvement is never fabricated.

These exercise the real institution-scoping flow end to end: a platform
"admin" creates two tpo_admin accounts for two different colleges, each TPO
sets their own password, and we assert TPO A can never see/touch anything
belonging to TPO B's institution - even by guessing IDs.
"""
import uuid

import pytest


def _create_tpo(client, admin_headers, email, college_name):
    """Creates a tpo_admin account (forced through the temp-password ->
    change-password flow, mirroring the real onboarding path) and returns
    auth headers for that TPO."""
    create_res = client.post("/api/v1/admin/create-admin", json={
        "name": f"TPO for {college_name}", "email": email, "role": "tpo_admin", "college_name": college_name,
    }, headers=admin_headers)
    assert create_res.status_code == 200, create_res.text
    temp_password = create_res.json()["temp_password"]

    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": email, "password": temp_password,
    })
    restricted_token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/v1/auth/change-password",
        json={"new_password": "tpoPassword123"},
        headers={"Authorization": f"Bearer {restricted_token}"},
    )
    assert change_res.status_code == 200, change_res.text
    full_token = change_res.json()["access_token"]
    return {"Authorization": f"Bearer {full_token}"}


def _register_student(client, email, college_name, name="Student"):
    res = client.post("/api/v1/auth/register", json={
        "name": name, "email": email, "password": "studentpass123",
        "branch": "CSE", "grad_year": 2027, "college_name": college_name,
    })
    assert res.status_code == 200, res.text
    login_res = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": email, "password": "studentpass123",
    })
    token = login_res.json()["access_token"]
    return res.json()["id"], {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def two_institution_setup(client, admin_user):
    """Two colleges, one TPO each, one student each - the base fixture for
    every isolation test below."""
    suffix = uuid.uuid4().hex[:8]
    tpo_a_headers = _create_tpo(client, admin_user["headers"], f"tpoA-{suffix}@example.com", f"Institution A {suffix}")
    tpo_b_headers = _create_tpo(client, admin_user["headers"], f"tpoB-{suffix}@example.com", f"Institution B {suffix}")

    student_a_id, student_a_headers = _register_student(client, f"studentA-{suffix}@example.com", f"Institution A {suffix}", "Student A")
    student_b_id, student_b_headers = _register_student(client, f"studentB-{suffix}@example.com", f"Institution B {suffix}", "Student B")

    return {
        "tpo_a": tpo_a_headers, "tpo_b": tpo_b_headers,
        "student_a_id": student_a_id, "student_a": student_a_headers,
        "student_b_id": student_b_id, "student_b": student_b_headers,
    }


def test_tpo_a_sees_only_institution_a_students(client, two_institution_setup):
    s = two_institution_setup
    res = client.get("/api/v1/tpo/dashboard", headers=s["tpo_a"])
    assert res.status_code == 200
    emails = [row["email"] for row in res.json()["all_students"]]
    assert any("studentA-" in e for e in emails)
    assert not any("studentB-" in e for e in emails)


def test_tpo_b_sees_only_institution_b_students(client, two_institution_setup):
    s = two_institution_setup
    res = client.get("/api/v1/tpo/dashboard", headers=s["tpo_b"])
    assert res.status_code == 200
    emails = [row["email"] for row in res.json()["all_students"]]
    assert any("studentB-" in e for e in emails)
    assert not any("studentA-" in e for e in emails)


def test_tpo_a_cannot_create_intervention_targeting_institution_b_student(client, two_institution_setup):
    s = two_institution_setup
    res = client.post("/api/v1/tpo/interventions", json={
        "title": "Cross-tenant DSA Workshop",
        "skill_topic": "DSA",
        "target_student_ids": [s["student_b_id"]],
    }, headers=s["tpo_a"])
    assert res.status_code == 403


def test_tpo_a_cannot_view_institution_b_intervention_by_id(client, two_institution_setup):
    s = two_institution_setup
    create_res = client.post("/api/v1/tpo/interventions", json={
        "title": "B-only Workshop",
        "skill_topic": "DSA",
        "target_student_ids": [s["student_b_id"]],
    }, headers=s["tpo_b"])
    assert create_res.status_code == 200
    intervention_id = create_res.json()["id"]

    # IDOR probe: TPO A guesses/knows institution B's intervention ID.
    get_res = client.get(f"/api/v1/tpo/interventions/{intervention_id}", headers=s["tpo_a"])
    assert get_res.status_code == 404  # not 403 - existence itself isn't confirmed

    complete_res = client.post(f"/api/v1/tpo/interventions/{intervention_id}/complete", headers=s["tpo_a"])
    assert complete_res.status_code == 404

    list_res = client.get("/api/v1/tpo/interventions", headers=s["tpo_a"])
    assert list_res.status_code == 200
    assert intervention_id not in [item["id"] for item in list_res.json()]


def test_tpo_a_export_excludes_institution_b_students(client, two_institution_setup):
    s = two_institution_setup
    res = client.get("/api/v1/tpo/export", headers=s["tpo_a"])
    assert res.status_code == 200
    csv_text = res.text
    assert "studentA-" in csv_text
    assert "studentB-" not in csv_text


def test_student_cannot_access_tpo_dashboard(client, two_institution_setup):
    s = two_institution_setup
    res = client.get("/api/v1/tpo/dashboard", headers=s["student_a"])
    assert res.status_code == 403


def test_student_cannot_create_intervention(client, two_institution_setup):
    s = two_institution_setup
    res = client.post("/api/v1/tpo/interventions", json={
        "title": "Self-granted workshop", "skill_topic": "DSA", "target_student_ids": [],
    }, headers=s["student_a"])
    assert res.status_code == 403


def test_intervention_with_no_reassessment_reports_no_improvement(client, two_institution_setup):
    """Core Phase 2 requirement: completing an intervention with zero
    post-intervention readiness data must NOT invent an improvement number."""
    s = two_institution_setup
    create_res = client.post("/api/v1/tpo/interventions", json={
        "title": "DSA Bootcamp", "skill_topic": "DSA", "target_student_ids": [s["student_a_id"]],
    }, headers=s["tpo_a"])
    assert create_res.status_code == 200
    body = create_res.json()
    # Student A has never taken an assessment, so there is no real baseline.
    assert body["pre_avg_score"] is None
    assert body["eligible_count"] == 1
    assert body["pre_assessed_count"] == 0
    intervention_id = body["id"]

    complete_res = client.post(f"/api/v1/tpo/interventions/{intervention_id}/complete", headers=s["tpo_a"])
    assert complete_res.status_code == 200
    completed = complete_res.json()
    assert completed["post_avg_score"] is None
    assert completed["improvement_delta"] is None
    assert completed["reassessed_count"] == 0


def test_intervention_improvement_uses_only_real_reassessment_data(client, two_institution_setup):
    s = two_institution_setup

    # Give student A a real baseline readiness score before the intervention.
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 30},
                headers=s["student_a"])
    client.post("/api/v1/quiz/submit", json={"subject": "Aptitude", "score_percent": 30},
                headers=s["student_a"])
    client.post("/api/v1/readiness/compute", headers=s["student_a"])

    create_res = client.post("/api/v1/tpo/interventions", json={
        "title": "DSA Bootcamp", "skill_topic": "DSA", "target_student_ids": [s["student_a_id"]],
    }, headers=s["tpo_a"])
    body = create_res.json()
    assert body["pre_avg_score"] == 30
    intervention_id = body["id"]

    # Student reassesses after the intervention with a real, improved score.
    client.post("/api/v1/quiz/submit", json={"subject": "DSA", "score_percent": 70},
                headers=s["student_a"])
    client.post("/api/v1/quiz/submit", json={"subject": "Aptitude", "score_percent": 70},
                headers=s["student_a"])
    client.post("/api/v1/readiness/compute", headers=s["student_a"])

    complete_res = client.post(f"/api/v1/tpo/interventions/{intervention_id}/complete", headers=s["tpo_a"])
    completed = complete_res.json()
    # Readiness quiz scores average across all attempts for that subject, so
    # DSA/Aptitude each become mean(30, 70) = 50 after the second attempt -
    # the point of this test is that the number comes from that real
    # computation, not a hardcoded +18/+20 improvement.
    assert completed["post_avg_score"] == 50
    assert completed["improvement_delta"] == 20  # 50 - 30, computed from real data only
    assert completed["reassessed_count"] == 1
