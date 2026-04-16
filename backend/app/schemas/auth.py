from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.schemas.tenant import TenantRead


class TenantRegisterRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=150)
    business_slug: str = Field(pattern=r"^[a-z0-9-]+$", min_length=2, max_length=100)
    admin_name: str = Field(min_length=2, max_length=150)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str | None = None
    tenant_id: int | None = None
    role: str | None = None


class UserRead(BaseModel):
    id: int
    tenant_id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    tenant: TenantRead | None = None

    model_config = ConfigDict(from_attributes=True)


class RegistrationResponse(BaseModel):
    tenant: TenantRead
    admin_user: UserRead
    message: str


class UserCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="user", pattern=r"^(admin|manager|user|auditor)$")
