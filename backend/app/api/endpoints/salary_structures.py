from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.employee import Employee
from backend.app.models.salary_structure import SalaryStructure
from backend.app.models.user import User
from backend.app.schemas.salary import SalaryStructureCreate, SalaryStructureRead, SalaryStructureUpdate

router = APIRouter()


def get_employee_or_404(db: Session, tenant_id: int, employee_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id, Employee.tenant_id == tenant_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("/", response_model=SalaryStructureRead, status_code=status.HTTP_201_CREATED)
def create_salary_structure(
    payload: SalaryStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    get_employee_or_404(db, current_user.tenant_id, payload.employee_id)

    existing = (
        db.query(SalaryStructure)
        .filter(SalaryStructure.tenant_id == current_user.tenant_id, SalaryStructure.employee_id == payload.employee_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Salary structure already exists for this employee")

    salary_structure = SalaryStructure(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(salary_structure)
    db.commit()
    db.refresh(salary_structure)
    return salary_structure


@router.get("/", response_model=list[SalaryStructureRead])
def list_salary_structures(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(SalaryStructure)
        .filter(SalaryStructure.tenant_id == current_user.tenant_id)
        .order_by(SalaryStructure.created_at.desc())
        .all()
    )


@router.get("/{employee_id}", response_model=SalaryStructureRead)
def get_salary_structure(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    salary_structure = (
        db.query(SalaryStructure)
        .filter(SalaryStructure.tenant_id == current_user.tenant_id, SalaryStructure.employee_id == employee_id)
        .first()
    )
    if not salary_structure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary structure not found")
    return salary_structure


@router.put("/{employee_id}", response_model=SalaryStructureRead)
def update_salary_structure(
    employee_id: int,
    payload: SalaryStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    salary_structure = (
        db.query(SalaryStructure)
        .filter(SalaryStructure.tenant_id == current_user.tenant_id, SalaryStructure.employee_id == employee_id)
        .first()
    )
    if not salary_structure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary structure not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(salary_structure, field, value)

    db.add(salary_structure)
    db.commit()
    db.refresh(salary_structure)
    return salary_structure
