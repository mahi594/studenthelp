"""Tenant isolation for /leetcode/admin/students and the daily-solve
notification fanout - both previously used the free-text college_name
(or, for notifications, nothing at all) instead of institution_id, which
could leak one institution's student activity to another institution's TPO.
"""
from tests.test_tpo import _create_tpo, _register_student
import uuid


def test_leetcode_admin_tracker_scoped_to_institution(client, admin_user):
    suffix = uuid.uuid4().hex[:8]
    tpo_a = _create_tpo(client, admin_user["headers"], f"lc-tpoA-{suffix}@example.com", f"LC Institution A {suffix}")
    tpo_b = _create_tpo(client, admin_user["headers"], f"lc-tpoB-{suffix}@example.com", f"LC Institution B {suffix}")

    _, student_a_headers = _register_student(client, f"lc-studentA-{suffix}@example.com", f"LC Institution A {suffix}", "LC Student A")
    _, student_b_headers = _register_student(client, f"lc-studentB-{suffix}@example.com", f"LC Institution B {suffix}", "LC Student B")

    client.post("/api/v1/leetcode/log", json={"problem_title": "Two Sum", "difficulty": "Easy"}, headers=student_a_headers)
    client.post("/api/v1/leetcode/log", json={"problem_title": "Reverse LinkedList", "difficulty": "Easy"}, headers=student_b_headers)

    res_a = client.get("/api/v1/leetcode/admin/students", headers=tpo_a)
    assert res_a.status_code == 200
    emails_a = [s["email"] for s in res_a.json()]
    assert any("lc-studentA-" in e for e in emails_a)
    assert not any("lc-studentB-" in e for e in emails_a)

    res_b = client.get("/api/v1/leetcode/admin/students", headers=tpo_b)
    emails_b = [s["email"] for s in res_b.json()]
    assert any("lc-studentB-" in e for e in emails_b)
    assert not any("lc-studentA-" in e for e in emails_b)


def test_leetcode_solve_notifies_only_own_institution_tpo(client, db_session, admin_user):
    """Previously every tpo_admin across every institution got notified
    whenever any student anywhere logged a solve."""
    from app.models.user import User
    from app.models.notification import Notification

    suffix = uuid.uuid4().hex[:8]
    tpo_a = _create_tpo(client, admin_user["headers"], f"lc2-tpoA-{suffix}@example.com", f"LC2 Institution A {suffix}")
    tpo_b = _create_tpo(client, admin_user["headers"], f"lc2-tpoB-{suffix}@example.com", f"LC2 Institution B {suffix}")

    student_a_id, student_a_headers = _register_student(client, f"lc2-studentA-{suffix}@example.com", f"LC2 Institution A {suffix}", "LC2 Student A")

    client.post("/api/v1/leetcode/log", json={"problem_title": "Two Sum", "difficulty": "Easy"}, headers=student_a_headers)

    tpo_a_user = db_session.query(User).filter(User.email == f"lc2-tpoA-{suffix}@example.com").first()
    tpo_b_user = db_session.query(User).filter(User.email == f"lc2-tpoB-{suffix}@example.com").first()

    tpo_a_notified = db_session.query(Notification).filter(
        Notification.user_id == tpo_a_user.id, Notification.type == "leetcode_daily_solved"
    ).first()
    tpo_b_notified = db_session.query(Notification).filter(
        Notification.user_id == tpo_b_user.id, Notification.type == "leetcode_daily_solved"
    ).first()

    assert tpo_a_notified is not None  # same institution as the student - should be notified
    assert tpo_b_notified is None  # different institution - must NOT be notified
