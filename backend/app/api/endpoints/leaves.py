from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_admin_or_manager, require_write
from backend.app.db.session import get_db
from backend.app.models.employee import Employee
from backend.app.models.leave import LeaveRequest
from backend.app.models.user import User
from backend.app.schemas.leave import LeaveRequestCreate, LeaveRequestRead, LeaveRequestUpdate

router = APIRouter()


def _get_or_404(db: Session, tenant_id: int, leave_id: int) -> LeaveRequest:
    lr = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id, LeaveRequest.tenant_id == tenant_id).first()
    if not lr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    return lr


@router.post("/", response_model=LeaveRequestRead, status_code=status.HTTP_201_CREATED)
def create_leave(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    emp = db.query(Employee).filter(
        Employee.id == payload.employee_id, Employee.tenant_id == current_user.tenant_id
    ).first()
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    days = (payload.end_date - payload.start_date).days + 1
    lr = LeaveRequest(
        tenant_id=current_user.tenant_id,
        employee_id=payload.employee_id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days=days,
        reason=payload.reason,
        status="pending",
    )
    db.add(lr)
    db.commit()
    return db.query(LeaveRequest).options(joinedload(LeaveRequest.employee)).filter(LeaveRequest.id == lr.id).first()


@router.get("/", response_model=list[LeaveRequestRead])
def list_leaves(
    employee_id: int | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(LeaveRequest).options(joinedload(LeaveRequest.employee)).filter(
        LeaveRequest.tenant_id == current_user.tenant_id
    )
    if employee_id:
        q = q.filter(LeaveRequest.employee_id == employee_id)
    if status_filter:
        q = q.filter(LeaveRequest.status == status_filter)
    return q.order_by(LeaveRequest.created_at.desc()).all()


@router.put("/{leave_id}/approve", response_model=LeaveRequestRead)
def approve_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    lr = _get_or_404(db, current_user.tenant_id, leave_id)
    lr.status = "approved"
    db.commit()
    return db.query(LeaveRequest).options(joinedload(LeaveRequest.employee)).filter(LeaveRequest.id == lr.id).first()


@router.put("/{leave_id}/reject", response_model=LeaveRequestRead)
def reject_leave(
    leave_id: int,
    payload: LeaveRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    lr = _get_or_404(db, current_user.tenant_id, leave_id)
    lr.status = "rejected"
    if payload.approver_comment is not None:
        lr.approver_comment = payload.approver_comment
    db.commit()
    return db.query(LeaveRequest).options(joinedload(LeaveRequest.employee)).filter(LeaveRequest.id == lr.id).first()


@router.delete("/{leave_id}")
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    lr = _get_or_404(db, current_user.tenant_id, leave_id)
    db.delete(lr)
    db.commit()
    return {"message": "Leave request deleted"}
