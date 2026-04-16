from datetime import date as date_cls, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.audit import AuditLog
from backend.app.models.user import User
from backend.app.schemas.audit import AuditLogRead

router = APIRouter()


@router.get("/", response_model=list[AuditLogRead])
def list_audit_logs(
    action: str | None = None,
    resource_type: str | None = None,
    user_id: int | None = None,
    days: int = 30,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent audit log entries. Default: last 30 days, max 200 rows."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    q = db.query(AuditLog).filter(
        AuditLog.tenant_id == current_user.tenant_id,
        AuditLog.created_at >= cutoff,
    )
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
