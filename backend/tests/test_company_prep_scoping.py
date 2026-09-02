import pytest
import uuid
from app.models.user import User
from app.models.institution import Institution
from app.models.company import Company
from app.models.prep_plan import PrepPlan
from app.api.v1.endpoints.auth import hash_password

def test_company_prep_plan_scoping(client, db_session):
    inst = Institution(name="Company Tech", code="COMP2026")
    db_session.add(inst)
    db_session.commit()

    pwd = hash_password("password123")

    student = User(name="Company Student", email="comp_student@tech.edu", hashed_password=pwd, role="student", institution_id=inst.id)
    db_session.add(student)
    db_session.commit()

    comp_a = Company(name="Company Alpha", roles=["Dev"])
    comp_b = Company(name="Company Beta", roles=["Analyst"])
    db_session.add_all([comp_a, comp_b])
    db_session.commit()

    plan_a = PrepPlan(user_id=student.id, target_company_id=comp_a.id, days_total=7, tasks=[{"day": 1, "topic": "DSA"}])
    plan_b = PrepPlan(user_id=student.id, target_company_id=comp_b.id, days_total=14, tasks=[{"day": 1, "topic": "SQL"}])
    db_session.add_all([plan_a, plan_b])
    db_session.commit()

    token = client.post("/api/v1/auth/login", data={"username": student.email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_a = client.get(f"/api/v1/prep-plan/latest?company_id={comp_a.id}", headers=headers)
    assert res_a.status_code == 200, res_a.text
    assert res_a.json()["target_company_id"] == str(comp_a.id)
    assert res_a.json()["days_total"] == 7

    res_b = client.get(f"/api/v1/prep-plan/latest?company_id={comp_b.id}", headers=headers)
    assert res_b.status_code == 200, res_b.text
    assert res_b.json()["target_company_id"] == str(comp_b.id)
    assert res_b.json()["days_total"] == 14

    # Verify Company-Scoped Resume Match
    from app.models.resume import Resume
    resume_a = Resume(user_id=student.id, target_company_id=comp_a.id, file_url="http://storage/res_a.pdf", parsed_text="Python", match_result={"match_score_percent": 85})
    resume_b = Resume(user_id=student.id, target_company_id=comp_b.id, file_url="http://storage/res_b.pdf", parsed_text="SQL", match_result={"match_score_percent": 60})
    db_session.add_all([resume_a, resume_b])
    db_session.commit()

    res_res_a = client.get(f"/api/v1/resume/latest?target_company_id={comp_a.id}", headers=headers)
    assert res_res_a.status_code == 200
    assert res_res_a.json()["target_company_id"] == str(comp_a.id)
    assert res_res_a.json()["match_result"]["match_score_percent"] == 85

    res_res_b = client.get(f"/api/v1/resume/latest?target_company_id={comp_b.id}", headers=headers)
    assert res_res_b.status_code == 200
    assert res_res_b.json()["target_company_id"] == str(comp_b.id)
    assert res_res_b.json()["match_result"]["match_score_percent"] == 60

    # Unmatched company should return null (empty state)
    comp_c = Company(name="Company Gamma", roles=["QA"])
    db_session.add(comp_c)
    db_session.commit()

    res_res_c = client.get(f"/api/v1/resume/latest?target_company_id={comp_c.id}", headers=headers)
    assert res_res_c.status_code == 200
    assert res_res_c.json() is None
