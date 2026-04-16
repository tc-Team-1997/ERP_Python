from collections import defaultdict
from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import extract
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.attendance import Attendance
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.schemas.attendance import (
    AttendanceCreate, AttendanceRead, AttendanceSummary, AttendanceUpdate,
)

router = APIRouter()


def _get_or_404(db: Session, tenant_id: int, att_id: int) -> Attendance:
    att = db.query(Attendance).filter(Attendance.id == att_id, Attendance.tenant_id == tenant_id).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    return att


@router.post("/", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def create_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    emp = db.query(Employee).filter(
        Employee.id == payload.employee_id, Employee.tenant_id == current_user.tenant_id
    ).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    existing = db.query(Attendance).filter(
        Attendance.tenant_id == current_user.tenant_id,
        Attendance.employee_id == payload.employee_id,
        Attendance.date == payload.date,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attendance already recorded for this date")

    att = Attendance(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(att)
    db.commit()
    return db.query(Attendance).options(joinedload(Attendance.employee)).filter(Attendance.id == att.id).first()


@router.get("/", response_model=list[AttendanceRead])
def list_attendance(
    employee_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Attendance).options(joinedload(Attendance.employee)).filter(
        Attendance.tenant_id == current_user.tenant_id
    )
    if employee_id:
        q = q.filter(Attendance.employee_id == employee_id)
    if year:
        q = q.filter(extract("year", Attendance.date) == year)
    if month:
        q = q.filter(extract("month", Attendance.date) == month)
    return q.order_by(Attendance.date.desc()).all()


@router.get("/summary", response_model=list[AttendanceSummary])
def attendance_summary(
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Attendance).options(joinedload(Attendance.employee)).filter(
        Attendance.tenant_id == current_user.tenant_id
    )
    if year:
        q = q.filter(extract("year", Attendance.date) == year)
    if month:
        q = q.filter(extract("month", Attendance.date) == month)

    buckets: dict[int, dict] = defaultdict(lambda: {"present": 0, "absent": 0, "half_day": 0, "leave": 0, "name": "—"})
    for att in q.all():
        b = buckets[att.employee_id]
        if att.employee:
            b["name"] = att.employee.full_name
        b[att.status] = b.get(att.status, 0) + 1

    return [
        AttendanceSummary(
            employee_id=eid,
            employee_name=b["name"],
            present=b["present"], absent=b["absent"],
            half_day=b["half_day"], leave=b["leave"],
            total_days=b["present"] + b["absent"] + b["half_day"] + b["leave"],
        )
        for eid, b in buckets.items()
    ]


@router.put("/{att_id}", response_model=AttendanceRead)
def update_attendance(
    att_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    att = _get_or_404(db, current_user.tenant_id, att_id)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(att, f, v)
    db.commit()
    return db.query(Attendance).options(joinedload(Attendance.employee)).filter(Attendance.id == att.id).first()


@router.delete("/{att_id}")
def delete_attendance(
    att_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    att = _get_or_404(db, current_user.tenant_id, att_id)
    db.delete(att)
    db.commit()
    return {"message": "Attendance deleted"}
