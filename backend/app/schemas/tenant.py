from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TenantRead(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
