"""
Institution resolution helper.

StudentHelp is multi-tenant per institution (college). Every user that
belongs to a college - student or TPO - must be linked via `institution_id`
to an `Institution` row, because that FK is the ONLY thing tenant-isolation
queries are allowed to trust (see tpo.py). `college_name` remains a
human-readable free-text field for display, but it is never used for
authorization.

This resolver is intentionally simple: it matches an existing institution by
case-insensitive name, or creates one if it doesn't exist yet. It does not
attempt fuzzy matching - a placement cell configuring a new institution name
is expected to be consistent (e.g. copy-pasted from an admin invite), and
mismatches are a data-entry problem to catch via the TPO admin UI, not
something to silently guess around.
"""
from sqlalchemy.orm import Session

from app.models.institution import Institution


def get_or_create_institution(db: Session, name: str) -> Institution:
    name = (name or "").strip()
    if not name:
        raise ValueError("Institution name must not be empty")

    existing = (
        db.query(Institution)
        .filter(Institution.name.ilike(name))
        .first()
    )
    if existing:
        return existing

    institution = Institution(name=name)
    db.add(institution)
    db.flush()  # get institution.id without a full commit, caller controls the transaction
    return institution
