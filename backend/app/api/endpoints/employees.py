from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate

router = APIRouter()


def get_employee_or_404(db: Session, tenant_id: int, employee_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id, Employee.tenant_id == tenant_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("/", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = (
        db.query(Employee)
        .filter(Employee.tenant_id == current_user.tenant_id, Employee.employee_code == payload.employee_code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee code already exists")

    employee = Employee(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/", response_model=list[EmployeeRead])
def list_employees(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Employee)
        .filter(Employee.tenant_id == current_user.tenant_id)
        .order_by(Employee.created_at.desc())
        .all()
    )


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_employee_or_404(db, current_user.tenant_id, employee_id)


@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    employee = get_employee_or_404(db, current_user.tenant_id, employee_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    employee = get_employee_or_404(db, current_user.tenant_id, employee_id)
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}
