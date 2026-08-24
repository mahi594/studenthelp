import io

import pytest
from pypdf import PdfWriter


def _make_pdf_bytes() -> bytes:
    """A minimal valid single-page PDF, good enough for PdfReader to parse
    without error (the endpoint doesn't require non-empty extracted text)."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _make_company(client, admin_user, name="Resume Test Corp"):
    res = client.post("/api/v1/companies/", json={
        "name": name,
        "roles": ["SDE-1"],
        "min_cgpa": "7.0",
        "preferred_branches": ["CSE"],
        "resume_keywords": ["DSA", "Docker"],
    }, headers=admin_user["headers"])
    return res.json()["id"]


@pytest.fixture(autouse=True)
def mock_storage(mocker):
    """Resume upload hits S3/R2 via storage_service.upload_resume - not
    configured in the test environment (and shouldn't make real network
    calls in tests regardless), so it's mocked here the same way AI calls
    are mocked in conftest.py's mock_ai fixture."""
    mocker.patch(
        "app.api.v1.endpoints.resume.upload_resume",
        return_value={"url": "https://fake-bucket.example.com/resumes/fake-key.pdf", "key": "resumes/fake-key.pdf"},
    )


def test_upload_and_match_resume(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)

    res = client.post(
        "/api/v1/resume/upload-and-match",
        data={"target_company_id": company_id},
        files={"file": ("resume.pdf", _make_pdf_bytes(), "application/pdf")},
        headers=registered_user["headers"],
    )

    assert res.status_code == 200
    body = res.json()
    assert body["file_url"] == "https://fake-bucket.example.com/resumes/fake-key.pdf"
    # Comes from the mocked match_resume_to_company fixture in conftest.py
    assert body["match_result"]["match_score_percent"] == 72
    assert body["match_result"]["meets_cgpa_cutoff"] is True


def test_upload_resume_requires_valid_company(client, registered_user):
    res = client.post(
        "/api/v1/resume/upload-and-match",
        data={"target_company_id": "00000000-0000-0000-0000-000000000000"},
        files={"file": ("resume.pdf", _make_pdf_bytes(), "application/pdf")},
        headers=registered_user["headers"],
    )
    assert res.status_code == 404


def test_unauthenticated_user_cannot_upload_resume(client, admin_user):
    company_id = _make_company(client, admin_user)
    res = client.post(
        "/api/v1/resume/upload-and-match",
        data={"target_company_id": company_id},
        files={"file": ("resume.pdf", _make_pdf_bytes(), "application/pdf")},
    )
    assert res.status_code == 401


def test_refresh_resume_url_requires_ownership(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)
    upload_res = client.post(
        "/api/v1/resume/upload-and-match",
        data={"target_company_id": company_id},
        files={"file": ("resume.pdf", _make_pdf_bytes(), "application/pdf")},
        headers=registered_user["headers"],
    )
    resume_id = upload_res.json()["id"]

    # A second student shouldn't be able to refresh someone else's resume URL
    client.post("/api/v1/auth/register", json={
        "name": "Other Student", "email": "other-resume-owner@example.com", "password": "otherpass123",
    })
    other_login = client.post("/api/v1/auth/login", data={
        "grant_type": "password", "username": "other-resume-owner@example.com", "password": "otherpass123",
    })
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    res = client.get(f"/api/v1/resume/{resume_id}/refresh-url", headers=other_headers)
    assert res.status_code == 404


def test_upload_rejects_non_pdf_extension(client, registered_user, admin_user):
    company_id = _make_company(client, admin_user)
    res = client.post(
        "/api/v1/resume/upload-and-match",
        data={"target_company_id": company_id},
        files={"file": ("resume.exe", b"MZ\x90\x00fake-exe-content", "application/octet-stream")},
        headers=registered_user["headers"],
    )
    assert res.status_code == 400


def test_upload_rejects_content_that_isnt_really_a_pdf(client, registered_user, admin_user):
    """Extension/MIME type say PDF, but the bytes don't start with the PDF
    signature - must be rejected by the magic-byte check, not trusted
    based on filename/declared content-type alone."""
    company_id = _make_company(client, admin_user)
    res = client.post(
        "/api/v1/resume/upload-and-match",
        data={"target_company_id": company_id},
        files={"file": ("resume.pdf", b"not actually a pdf file", "application/pdf")},
        headers=registered_user["headers"],
    )
    assert res.status_code == 400


def test_upload_rejects_oversized_file(client, registered_user, admin_user):
    from app.core.config import settings

    company_id = _make_company(client, admin_user)
    oversized = b"%PDF-1.4\n" + b"0" * (settings.MAX_RESUME_UPLOAD_BYTES + 1)
    res = client.post(
        "/api/v1/resume/upload-and-match",
        data={"target_company_id": company_id},
        files={"file": ("resume.pdf", oversized, "application/pdf")},
        headers=registered_user["headers"],
    )
    assert res.status_code == 400


def test_storage_key_ignores_path_traversal_in_filename():
    """A malicious filename like '../../etc/cron.d/evil.pdf' must never
    leak directory components into the generated storage key - the key is
    always confined to resumes/{user_id}/... regardless of what the
    uploader named their file."""
    from app.services.storage_service import _build_key

    key = _build_key("../../../etc/cron.d/evil.pdf", "user123")
    assert ".." not in key
    assert key.startswith("resumes/user123/")
    assert key.endswith(".pdf")
