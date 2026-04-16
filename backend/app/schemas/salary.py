from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SalaryStructureBase(BaseModel):
    basic: float = Field(ge=0)
    hra: float = Field(default=0, ge=0)
    allowances: float = Field(default=0, ge=0)
    deductions: float = Field(default=0, ge=0)
    tax_percent: float = Field(default=0, ge=0, le=100)
    effective_from: date


class SalaryStructureCreate(SalaryStructureBase):
    employee_id: int


class SalaryStructureUpdate(BaseModel):
    basic: float | None = Field(default=None, ge=0)
    hra: float | None = Field(default=None, ge=0)
    allowances: float | None = Field(default=None, ge=0)
    deductions: float | None = Field(default=None, ge=0)
    tax_percent: float | None = Field(default=None, ge=0, le=100)
    effective_from: date | None = None


class SalaryStructureRead(SalaryStructureBase):
    id: int
    tenant_id: int
    employee_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
