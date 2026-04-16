from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentVersionRead(BaseModel):
    id: int
    document_id: int
    version_number: int
    filename: str
    file_size: int
    mime_type: str | None = None
    change_notes: str | None = None
    uploaded_by: int | None = None
    uploaded_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    tags: str | None = None


class DocumentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    tags: str | None = None
    is_archived: bool | None = None


class DocumentRead(BaseModel):
    id: int
    tenant_id: int
    title: str
    description: str | None = None
    category: str | None = None
    tags: str | None = None
    current_version: int
    is_archived: bool
    created_by: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    versions: list[DocumentVersionRead] = []
    model_config = ConfigDict(from_attributes=True)
