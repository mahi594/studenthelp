"""
Job listing fetch service.

Pulls LIVE job openings from Adzuna's free API (https://developer.adzuna.com)
and stores them as `JobListing` rows with a direct apply link. This is
deliberately separate from the curated `Company`/`Round` data - openings are
live/temporary (fetched, expire, get deleted), whereas interview-process
facts stay admin-curated and permanent.

Adzuna doesn't return an explicit "expires_at" - we default to 30 days from
fetch time and rely on the periodic cleanup below to remove stale listings.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job_listing import JobListing

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"
DEFAULT_LISTING_TTL_DAYS = 30


def fetch_listings_from_adzuna(
    keywords: str,
    location: str = "",
    results_per_page: int = 20,
    page: int = 1,
) -> List[Dict[str, Any]]:
    """Calls Adzuna's search endpoint. Raises requests.HTTPError on failure -
    caller should handle (e.g. surface a clear error if credentials are missing)."""
    if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
        raise RuntimeError(
            "ADZUNA_APP_ID / ADZUNA_APP_KEY not configured - get free credentials "
            "at https://developer.adzuna.com and add them to .env"
        )

    url = f"{ADZUNA_BASE_URL}/{settings.ADZUNA_COUNTRY}/search/{page}"
    params = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": keywords,
        "where": location,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("results", [])


def upsert_job_listings(raw_results: List[Dict[str, Any]], db: Session) -> Dict[str, int]:
    """Inserts new listings, skips ones already stored (deduped by Adzuna's
    external id). Returns counts for reporting back to the admin."""
    created = 0
    skipped = 0

    for item in raw_results:
        external_id = str(item.get("id"))
        if not external_id:
            continue

        existing = db.query(JobListing).filter(JobListing.external_id == external_id).first()
        if existing:
            skipped += 1
            continue

        company_name = (item.get("company") or {}).get("display_name", "Unknown")
        role_title = item.get("title", "Untitled role")
        location = (item.get("location") or {}).get("display_name")
        apply_url = item.get("redirect_url")
        if not apply_url:
            continue  # a listing with no apply link isn't useful, skip it

        posted_at = None
        if item.get("created"):
            try:
                posted_at = datetime.fromisoformat(item["created"].replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                posted_at = None

        listing = JobListing(
            source="adzuna",
            external_id=external_id,
            company_name=company_name,
            role_title=role_title,
            location=location,
            description_snippet=(item.get("description") or "")[:500],
            apply_url=apply_url,
            posted_at=posted_at,
            expires_at=datetime.utcnow() + timedelta(days=DEFAULT_LISTING_TTL_DAYS),
        )
        db.add(listing)
        created += 1

    db.commit()
    return {"created": created, "skipped_duplicates": skipped}


def delete_expired_listings(db: Session) -> int:
    """Deletes any listing past its expiry. Call this on every refresh (and
    optionally on a schedule - see docs/architecture.md for how to automate
    this on Windows/Linux since there's no built-in cron in this scaffold)."""
    deleted = db.query(JobListing).filter(JobListing.expires_at < datetime.utcnow()).delete()
    db.commit()
    return deleted
