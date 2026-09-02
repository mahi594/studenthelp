import uuid
import pytest
from app.models.user import User
from app.models.institution import Institution
from app.models.readiness import ReadinessScore
from app.api.v1.endpoints.auth import hash_password

def test_tpo_sql_filtering_and_pagination(client, db_session):
    inst = Institution(name="SQL Filter Tech", code="SQL2026")
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    pwd = hash_password("password123")

    tpo = User(
        name="TPO Admin",
        email="tpo_sql@tech.edu",
        hashed_password=pwd,
        role="tpo_admin",
        institution_id=inst.id,
    )
    db_session.add(tpo)
    db_session.commit()

    students = []
    for i in range(550):
        branch = "CSE" if i < 100 else "ECE"
        grad_year = 2026 if i % 2 == 0 else 2027
        s = User(
            name=f"Student {i:03d}",
            email=f"student{i}@sql.edu",
            hashed_password=pwd,
            role="student",
            institution_id=inst.id,
            branch=branch,
            grad_year=grad_year,
            cgpa="8.5" if i < 200 else "6.0",
        )
        students.append(s)
    db_session.bulk_save_objects(students)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", data={"username": tpo.email, "password": "password123"})
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/tpo/dashboard?branch=CSE&page=1&page_size=20", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["total_matching"] == 100
    assert len(data["all_students"]) == 20
    assert data["total_pages"] == 5

    res_p5 = client.get("/api/v1/tpo/dashboard?branch=CSE&page=5&page_size=20", headers=headers)
    assert res_p5.status_code == 200
    data_p5 = res_p5.json()
    assert len(data_p5["all_students"]) == 20
    assert data_p5["all_students"][0]["user_id"] != data["all_students"][0]["user_id"]
