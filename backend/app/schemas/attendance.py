from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.employee import EmployeeMini


class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    check_in: time | None = None
    check_out: time | None = None
    status: str = Field(default="present", pattern=r"^(present|absent|half_day|leave)$")
    notes: str | None = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    check_in: time | None = None
    check_out: time | None = None
    status: str | None = Field(default=None, pattern=r"^(present|absent|half_day|leave)$")
    notes: str | None = None


class AttendanceRead(AttendanceBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None
    employee: EmployeeMini | None = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceSummary(BaseModel):
    employee_id: int
    employee_name: str
    present: int
    absent: int
    half_day: int
    leave: int
    total_days: int
