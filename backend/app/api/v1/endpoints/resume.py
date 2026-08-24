import uuid
import io
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pypdf import PdfReader

from app.db.database import get_db
from app.models.company import Company
from app.models.resume import Resume
from app.models.user import User
from app.schemas.schemas import ResumeMatchOut
from app.services.ai_service import match_resume_to_company
from app.services.storage_service import upload_resume, get_presigned_resume_url, validate_pdf_content
from app.api.v1.endpoints.auth import get_current_user
from app.core.rate_limit import limiter
from app.core.config import settings

router = APIRouter(prefix="/resume", tags=["resume"])

ALLOWED_RESUME_EXTENSIONS = {".pdf"}
ALLOWED_RESUME_CONTENT_TYPES = {"application/pdf"}


@router.post("/upload-and-match", response_model=ResumeMatchOut)
@limiter.limit("5/minute")
def upload_and_match(
    request: Request,
    target_company_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == target_company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Extension + declared MIME type are checked first (cheap, and blocks
    # obviously-wrong uploads before we even read the body) - but neither is
    # trusted on its own, since both are attacker-controlled. The real check
    # is the PDF magic-byte signature below.
    original_name = file.filename or "resume.pdf"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF resumes are accepted.")
    if file.content_type and file.content_type not in ALLOWED_RESUME_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF resumes are accepted.")

    contents = file.file.read()

    # Size limit BEFORE any parsing work - rejects oversized uploads
    # cheaply instead of spending CPU on PDF parsing first.
    if len(contents) > settings.MAX_RESUME_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Resume file is too large. Maximum size is {settings.MAX_RESUME_UPLOAD_BYTES // (1024 * 1024)}MB.",
        )

    try:
        validate_pdf_content(contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        reader = PdfReader(io.BytesIO(contents))
        resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to parse text from PDF. Ensure the PDF is not encrypted or corrupted.")

    try:
        storage_result = upload_resume(
            file_bytes=contents,
            original_filename=original_name,
            user_id=current_user.id,
            content_type=file.content_type or "application/pdf",
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    match_result = match_resume_to_company(resume_text, company)

    resume = Resume(
        user_id=current_user.id,
        file_url=storage_result["url"],
        storage_key=storage_result["key"],
        parsed_text=resume_text,
        target_company_id=company.id,
        match_result=match_result,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/{resume_id}", response_model=ResumeMatchOut)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.storage_key:
        resume.file_url = get_presigned_resume_url(resume.storage_key)
    return resume


@router.get("/{resume_id}/refresh-url", response_model=ResumeMatchOut)
def refresh_resume_url(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regenerates a fresh presigned URL from stored storage_key."""
    return get_resume(resume_id, db, current_user)

