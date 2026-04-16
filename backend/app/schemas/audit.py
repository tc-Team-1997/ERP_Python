from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: int
    tenant_id: int
    user_id: int | None = None
    user_email: str | None = None
    action: str
    resource_type: str
    resource_id: int | None = None
    description: str | None = None
    ip_address: str | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
