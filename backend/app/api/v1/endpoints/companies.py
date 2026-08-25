import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.company import Company, Round
from app.models.user import User
from datetime import datetime
from app.schemas.schemas import CompanyOut, CompanyCreate, RoundCreate, RoundOut, CompanyVerifyRequest
from app.services.audit_log_service import log_event


from app.api.v1.endpoints.auth import get_current_admin_user, get_current_tpo_or_admin_user

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/{company_id}/verify", response_model=CompanyOut)
def verify_company(
    company_id: uuid.UUID,
    payload: CompanyVerifyRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_tpo_or_admin_user),
):

    """Admin/TPO-only: mark company profile as verified by placement cell."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.is_curated_verified = True
    company.source_type = payload.source_type
    company.verified_by = payload.verified_by
    company.verified_at = datetime.utcnow()
    company.confidence = payload.confidence

    db.commit()
    db.refresh(company)

    log_event(
        db=db,
        actor_user=current_admin,
        action="company_verified",
        resource_type="company",
        resource_id=str(company.id),
        metadata={"company_name": company.name, "verified_by": payload.verified_by},
    )

    return company



@router.get("/", response_model=List[CompanyOut])
def list_companies(
    name: Optional[str] = None,
    role: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List/search companies. Pass `q` or `name` to search by company name/role."""
    query = db.query(Company)
    search_term = q or name
    if search_term:
        query = query.filter(Company.name.ilike(f"%{search_term}%"))
    if role:
        query = query.filter(Company.roles.any(role))
    return query.all()



@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: uuid.UUID, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyOut)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Admin-only: add a curated company profile."""
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/{company_id}/rounds", response_model=CompanyOut)
def add_round(
    company_id: uuid.UUID,
    payload: RoundCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Admin-only: add one stage (OA / Technical / HR / ...) to a company's
    curated hiring process. Returns the full company so the frontend can
    just re-render the rounds list from the response."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    round_ = Round(company_id=company.id, **payload.model_dump())
    db.add(round_)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}/rounds/{round_id}", response_model=CompanyOut)
def delete_round(
    company_id: uuid.UUID,
    round_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    round_ = (
        db.query(Round)
        .filter(Round.id == round_id, Round.company_id == company_id)
        .first()
    )
    if not round_:
        raise HTTPException(status_code=404, detail="Round not found")

    db.delete(round_)
    db.commit()
    company = db.query(Company).filter(Company.id == company_id).first()
    return company
