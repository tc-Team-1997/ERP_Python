from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeBase(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr | None = None
    department: str | None = None
    designation: str | None = None
    joining_date: date
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    department: str | None = None
    designation: str | None = None
    joining_date: date | None = None
    is_active: bool | None = None


class EmployeeRead(EmployeeBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeMini(BaseModel):
    id: int
    employee_code: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)
