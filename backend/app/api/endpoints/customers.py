from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.customer import Customer
from backend.app.models.user import User
from backend.app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter()


def _get_or_404(db: Session, tenant_id: int, customer_id: int) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.tenant_id == tenant_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if payload.email:
        existing = (
            db.query(Customer)
            .filter(Customer.tenant_id == current_user.tenant_id, Customer.email == payload.email)
            .first()
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer with this email already exists")

    customer = Customer(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Customer)
        .filter(Customer.tenant_id == current_user.tenant_id)
        .order_by(Customer.created_at.desc())
        .all()
    )


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_or_404(db, current_user.tenant_id, customer_id)


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    customer = _get_or_404(db, current_user.tenant_id, customer_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    customer = _get_or_404(db, current_user.tenant_id, customer_id)
    db.delete(customer)
    db.commit()
    return {"message": "Customer deleted successfully"}
