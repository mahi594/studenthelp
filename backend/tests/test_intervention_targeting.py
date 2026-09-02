import uuid
import pytest
from app.models.user import User
from app.models.institution import Institution
from app.models.intervention import Intervention
from app.api.v1.endpoints.auth import hash_password

def test_criteria_intervention_page_independence(client, db_session):
    inst1 = Institution(name="Intervention Univ", code="INT2026")
    inst2 = Institution(name="Foreign Univ", code="FOR2026")
    db_session.add_all([inst1, inst2])
    db_session.commit()

    pwd = hash_password("password123")

    tpo1 = User(name="TPO One", email="tpo1@int.edu", hashed_password=pwd, role="tpo_admin", institution_id=inst1.id)
    tpo2 = User(name="TPO Two", email="tpo2@for.edu", hashed_password=pwd, role="tpo_admin", institution_id=inst2.id)
    db_session.add_all([tpo1, tpo2])
    db_session.commit()

    students = []
    for i in range(500):
        b = "CSE" if i < 100 else "ECE"
        students.append(User(name=f"Inst1 Stud {i}", email=f"i1_stud{i}@int.edu", hashed_password=pwd, role="student", institution_id=inst1.id, branch=b))
    
    foreign_student = User(name="Foreign Stud", email="foreign@for.edu", hashed_password=pwd, role="student", institution_id=inst2.id, branch="CSE")
    students.append(foreign_student)

    db_session.add_all(students)
    db_session.commit()

    token = client.post("/api/v1/auth/login", data={"username": tpo1.email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/tpo/interventions",
        json={"title": "DSA Workshop", "skill_topic": "dsa", "target_branch": "CSE", "target_student_ids": []},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data["target_student_ids"]) == 100

    valid_ids = [str(students[0].id), str(students[1].id)]
    res_b = client.post(
        "/api/v1/tpo/interventions",
        json={"title": "Explicit Session", "skill_topic": "cs", "target_student_ids": valid_ids},
        headers=headers,
    )
    assert res_b.status_code == 200
    assert len(res_b.json()["target_student_ids"]) == 2

    res_idor = client.post(
        "/api/v1/tpo/interventions",
        json={"title": "Attack", "skill_topic": "cs", "target_student_ids": [str(foreign_student.id)]},
        headers=headers,
    )
    assert res_idor.status_code == 403

    # Empty target IDs with no criteria must return HTTP 400 Bad Request
    res_empty = client.post(
        "/api/v1/tpo/interventions",
        json={"title": "No Criteria Session", "skill_topic": "dsa", "target_student_ids": []},
        headers=headers,
    )
    assert res_empty.status_code == 400
    assert "Provide targeting criteria or select at least one student." in res_empty.json()["detail"]
