"""Audit Log API Endpoint.

Restricted to TPO/Admin users. Scoped strictly to the current user's institution_id.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.schemas import AuditLogOut
from app.api.v1.endpoints.auth import get_current_tpo_or_admin_user

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("/", response_model=List[AuditLogOut])
def list_audit_logs(
    action: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_tpo_or_admin_user),
):
    """Lists institutional audit logs for the TPO's institution."""
    if not current_admin.institution_id:
        return []

    query = db.query(AuditLog).filter(AuditLog.institution_id == current_admin.institution_id)
    if action:
        query = query.filter(AuditLog.action == action)

    return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

