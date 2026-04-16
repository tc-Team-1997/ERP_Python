from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.employee import EmployeeMini


class PayrollProcessRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class PayrollRecordRead(BaseModel):
    id: int
    tenant_id: int
    employee_id: int
    month: int
    year: int
    basic: float
    hra: float
    allowances: float
    gross_salary: float
    deductions: float
    tax_amount: float
    net_salary: float
    status: str
    processed_at: datetime | None = None
    employee: EmployeeMini | None = None

    model_config = ConfigDict(from_attributes=True)
