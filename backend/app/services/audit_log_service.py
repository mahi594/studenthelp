"""Audit Log Service.

Records institutional events without logging sensitive data (no passwords, tokens, JWTs, resume text).
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


def log_event(
    db: Session,
    actor_user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[AuditLog]:
    """Records an audit event scoped to the actor's institution_id."""
    if not actor_user.institution_id:
        # User has no institution assigned yet - omit or log warning
        logger.warning("Attempted audit log for user %s with no institution_id", actor_user.id)
        return None

    audit_entry = AuditLog(
        institution_id=actor_user.institution_id,
        actor_user_id=actor_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata or {},
    )
    db.add(audit_entry)
    try:
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception as exc:
        db.rollback()
        logger.error("Failed to commit audit log event: %s", exc)
        return None
