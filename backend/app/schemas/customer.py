from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    gstin: str | None = Field(default=None, max_length=20)
    billing_address: str | None = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    gstin: str | None = Field(default=None, max_length=20)
    billing_address: str | None = None
    is_active: bool | None = None


class CustomerRead(CustomerBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerMini(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
