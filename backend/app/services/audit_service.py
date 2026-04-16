from sqlalchemy.orm import Session

from backend.app.models.audit import AuditLog
from backend.app.models.user import User


def log_event(
    db: Session,
    user: User | None,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    description: str | None = None,
    ip_address: str | None = None,
    commit: bool = True,
) -> AuditLog:
    """Write a row into the audit log. Call this from endpoints after mutations."""
    tenant_id = user.tenant_id if user else None
    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
