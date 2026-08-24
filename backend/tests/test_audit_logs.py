import uuid
from tests.test_tpo import _create_tpo, _register_student


def test_audit_log_created_on_verification_and_csv_export(client, admin_user):
    suffix = uuid.uuid4().hex[:8]
    college_name = f"Audit College {suffix}"
    tpo_headers = _create_tpo(client, admin_user["headers"], f"tpo-audit-{suffix}@example.com", college_name)

    # Verify company creates an audit log
    company_res = client.post("/api/v1/companies/", json={
        "name": f"Audit Test Corp {suffix}",
        "roles": ["SDE"],
    }, headers=admin_user["headers"])
    company_id = company_res.json()["id"]

    verify_res = client.post(f"/api/v1/companies/{company_id}/verify", json={
        "verified_by": "TPO Officer",
        "confidence": "High",
        "source_type": "placement_cell"
    }, headers=tpo_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["is_curated_verified"] is True
    assert verify_res.json()["source_type"] == "placement_cell"

    # Export CSV creates an audit log
    export_res = client.get("/api/v1/tpo/export", headers=tpo_headers)
    assert export_res.status_code == 200

    # Fetch audit logs as TPO
    audit_res = client.get("/api/v1/audit-logs/", headers=tpo_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 2
    actions = [log["action"] for log in logs]
    assert "company_verified" in actions
    assert "csv_export" in actions


def test_tpo_b_cannot_see_tpo_a_audit_logs(client, admin_user):
    suffix = uuid.uuid4().hex[:8]
    tpo_a_headers = _create_tpo(client, admin_user["headers"], f"tpoA-audit-{suffix}@example.com", f"Inst A {suffix}")
    tpo_b_headers = _create_tpo(client, admin_user["headers"], f"tpoB-audit-{suffix}@example.com", f"Inst B {suffix}")

    # TPO A generates a CSV export
    client.get("/api/v1/tpo/export", headers=tpo_a_headers)

    # TPO B lists audit logs - should not see TPO A's logs
    res_b = client.get("/api/v1/audit-logs/", headers=tpo_b_headers)
    assert res_b.status_code == 200
    logs_b = res_b.json()
    assert len(logs_b) == 0


def test_student_cannot_access_audit_logs(client, registered_user):
    res = client.get("/api/v1/audit-logs/", headers=registered_user["headers"])
    assert res.status_code == 403
