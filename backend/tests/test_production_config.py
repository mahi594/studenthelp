import pytest
from app.core.config import settings
from app.services.storage_service import upload_resume

def test_production_mode_requires_object_storage(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "S3_ACCESS_KEY_ID", "")
    monkeypatch.setattr(settings, "S3_SECRET_ACCESS_KEY", "")

    pdf_bytes = b"%PDF-1.4 header content"
    with pytest.raises(RuntimeError) as exc_info:
        upload_resume(pdf_bytes, "test.pdf", user_id="12345")
    
    assert "Object Storage" in str(exc_info.value)

def test_dev_mode_uses_local_storage(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "development")
    monkeypatch.setattr(settings, "S3_ACCESS_KEY_ID", "")
    monkeypatch.setattr(settings, "S3_SECRET_ACCESS_KEY", "")

    pdf_bytes = b"%PDF-1.4 header content"
    res = upload_resume(pdf_bytes, "test.pdf", user_id="12345")
    assert "url" in res
    assert "key" in res
