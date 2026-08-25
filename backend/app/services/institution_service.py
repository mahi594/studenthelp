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


def get_or_create_institution(db: Session, name_or_code: str, code: str = None) -> Institution:
    input_str = (name_or_code or "").strip()
    code_str = (code or "").strip()
    
    # 1. Match by code if provided
    if code_str:
        by_code = db.query(Institution).filter(Institution.code.ilike(code_str)).first()
        if by_code:
            return by_code

    # 2. Match by exact case-insensitive name
    if input_str:
        by_name = db.query(Institution).filter(Institution.name.ilike(input_str)).first()
        if by_name:
            return by_name
        # Also check if input_str was passed as a code
        by_code = db.query(Institution).filter(Institution.code.ilike(input_str)).first()
        if by_code:
            return by_code

    if not input_str and not code_str:
        raise ValueError("Institution name or valid code must be provided")

    # 3. Create institution
    inst_name = input_str or code_str
    inst_code = code_str if code_str else None
    institution = Institution(name=inst_name, code=inst_code)
    db.add(institution)
    db.flush()
    return institution


