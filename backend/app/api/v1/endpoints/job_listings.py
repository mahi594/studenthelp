import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.job_listing import JobListing
from app.schemas.schemas import (
    JobListingRefreshRequest,
    JobListingRefreshResponse,
    JobListingOut,
)
from app.services.job_listing_service import (
    fetch_listings_from_adzuna,
    upsert_job_listings,
    delete_expired_listings,
)
from app.api.v1.endpoints.auth import get_current_admin_user, get_current_user
from app.core.rate_limit import limiter

router = APIRouter(prefix="/job-listings", tags=["job-listings"])
logger = logging.getLogger(__name__)


@router.post("/refresh", response_model=JobListingRefreshResponse)
def refresh_job_listings(
    payload: JobListingRefreshRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """Admin-triggered: fetches current openings from Adzuna for the given
    keywords/location, stores new ones, and deletes anything already expired.
    Run this periodically (see docs/architecture.md for scheduling options -
    there's no built-in cron in this scaffold, so call this on a schedule
    yourself, e.g. Windows Task Scheduler hitting this endpoint daily)."""
    try:
        raw_results = fetch_listings_from_adzuna(
            keywords=payload.keywords,
            location=payload.location,
            results_per_page=payload.results_per_page,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        # Never leak the raw exception (could contain request URLs, partial
        # API keys, internal hostnames, etc.) to the client - log it
        # server-side and return a generic, friendly error instead.
        logger.exception("Failed to fetch job listings from external provider")
        raise HTTPException(status_code=502, detail="Failed to fetch job listings right now. Please try again shortly.")

    upsert_result = upsert_job_listings(raw_results, db)
    expired_deleted = delete_expired_listings(db)

    return JobListingRefreshResponse(
        fetched=len(raw_results),
        created=upsert_result["created"],
        skipped_duplicates=upsert_result["skipped_duplicates"],
        expired_deleted=expired_deleted,
    )


@router.get("/search", response_model=List[JobListingOut])
@limiter.limit("10/minute")
def search_job_listings(
    request: Request,
    keywords: str,
    location: Optional[str] = None,
    results_per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student-facing direct Adzuna search. Fetches live openings, persists them to local DB,
    and returns matching job listings to the student."""
    if not keywords or not keywords.strip():
        raise HTTPException(status_code=400, detail="Keywords parameter is required.")

    clean_keywords = keywords.strip()
    clean_location = (location or "").strip()
    clamped_results_per_page = max(1, min(results_per_page, 50))

    try:
        raw_results = fetch_listings_from_adzuna(
            keywords=clean_keywords,
            location=clean_location,
            results_per_page=clamped_results_per_page,
        )
    except RuntimeError as exc:
        # Configuration issues (e.g. missing credentials)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Failed to fetch job listings from external provider during student search")
        raise HTTPException(status_code=502, detail="Failed to fetch job listings right now. Please try again shortly.")

    if raw_results:
        upsert_job_listings(raw_results, db)

    # Return matching results sorted by posted_at
    query = db.query(JobListing)
    if clean_keywords:
        # Filter by keywords in role_title or description or company_name
        kw_filter = f"%{clean_keywords}%"
        query = query.filter(
            (JobListing.role_title.ilike(kw_filter)) |
            (JobListing.description_snippet.ilike(kw_filter)) |
            (JobListing.company_name.ilike(kw_filter))
        )
    if clean_location:
        query = query.filter(JobListing.location.ilike(f"%{clean_location}%"))

    results = query.order_by(JobListing.posted_at.desc()).limit(clamped_results_per_page).all()
    return results


@router.get("/", response_model=List[JobListingOut])
def browse_job_listings(
    company_name: Optional[str] = None,
    role: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student-facing browse/search over currently live listings (already-
    expired ones are removed by the cleanup step in /refresh, so anything
    returned here should still be open)."""
    query = db.query(JobListing)
    if company_name:
        query = query.filter(JobListing.company_name.ilike(f"%{company_name}%"))
    if role:
        query = query.filter(JobListing.role_title.ilike(f"%{role}%"))
    if location:
        query = query.filter(JobListing.location.ilike(f"%{location}%"))

    return query.order_by(JobListing.posted_at.desc()).limit(limit).all()

