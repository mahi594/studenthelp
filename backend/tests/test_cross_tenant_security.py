import pytest
import uuid
from app.models.user import User
from app.models.institution import Institution
from app.api.v1.endpoints.auth import hash_password

def test_cross_tenant_security_isolation(client, db_session):
    inst_a = Institution(name="Inst Alpha", code="ALPHA2026")
    inst_b = Institution(name="Inst Beta", code="BETA2026")
    db_session.add_all([inst_a, inst_b])
    db_session.commit()

    pwd = hash_password("password123")

    tpo_a = User(name="TPO Alpha", email="tpo@alpha.edu", hashed_password=pwd, role="tpo_admin", institution_id=inst_a.id)
    tpo_b = User(name="TPO Beta", email="tpo@beta.edu", hashed_password=pwd, role="tpo_admin", institution_id=inst_b.id)
    student_a = User(name="Student Alpha", email="student@alpha.edu", hashed_password=pwd, role="student", institution_id=inst_a.id)
    student_b = User(name="Student Beta", email="student@beta.edu", hashed_password=pwd, role="student", institution_id=inst_b.id)
    db_session.add_all([tpo_a, tpo_b, student_a, student_b])
    db_session.commit()

    token_a = client.post("/api/v1/auth/login", data={"username": tpo_a.email, "password": "password123"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res_detail = client.get(f"/api/v1/tpo/students/{student_b.id}", headers=headers_a)
    assert res_detail.status_code == 404

    res_list = client.get("/api/v1/tpo/dashboard", headers=headers_a)
    assert res_list.status_code == 200, res_list.text
    student_ids = [s["user_id"] for s in res_list.json()["all_students"]]
    assert str(student_a.id) in student_ids
    assert str(student_b.id) not in student_ids

    res_csv = client.get("/api/v1/tpo/export", headers=headers_a)
    assert res_csv.status_code == 200, res_csv.text
    assert "student@alpha.edu" in res_csv.text
    assert "student@beta.edu" not in res_csv.text
