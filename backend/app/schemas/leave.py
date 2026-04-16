from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.employee import EmployeeMini


class LeaveRequestBase(BaseModel):
    employee_id: int
    leave_type: str = Field(default="casual", pattern=r"^(casual|sick|earned|unpaid)$")
    start_date: date
    end_date: date
    reason: str | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(pending|approved|rejected|cancelled)$")
    approver_comment: str | None = None


class LeaveRequestRead(BaseModel):
    id: int
    tenant_id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    days: int
    reason: str | None = None
    status: str
    approver_comment: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    employee: EmployeeMini | None = None

    model_config = ConfigDict(from_attributes=True)
