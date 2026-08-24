from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.application import Application
from app.schemas.schemas import ApplicationMarkRequest, ApplicationOut
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/mark", response_model=ApplicationOut)
def mark_application_status(
    payload: ApplicationMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sets the student's application status for a company - e.g. call with
    status='applied' when they click 'Mark as Applied' after using the apply
    link. Upserts: re-calling just updates the existing row."""
    company = db.query(Company).filter(Company.id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    application = (
        db.query(Application)
        .filter(Application.user_id == current_user.id, Application.company_id == payload.company_id)
        .first()
    )

    if not application:
        application = Application(user_id=current_user.id, company_id=payload.company_id)
        db.add(application)

    application.status = payload.status
    if payload.status == "applied" and not application.applied_at:
        application.applied_at = datetime.utcnow()

    db.commit()
    db.refresh(application)
    return application


@router.get("/", response_model=List[ApplicationOut])
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Every company this student has any application status for - use this
    to build a {company_id: status} map on the frontend."""
    return db.query(Application).filter(Application.user_id == current_user.id).all()
