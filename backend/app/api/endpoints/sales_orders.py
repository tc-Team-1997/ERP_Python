from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.crm import SalesOrder, SalesOrderItem
from backend.app.models.customer import Customer
from backend.app.models.user import User
from backend.app.schemas.crm import SalesOrderCreate, SalesOrderRead, SalesOrderUpdate

router = APIRouter()
TWO = Decimal("0.01")


def _calc(items: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
    sub = Decimal(0)
    tax = Decimal(0)
    for it in items:
        qty = Decimal(str(it["quantity"]))
        price = Decimal(str(it["unit_price"]))
        line = (qty * price).quantize(TWO, rounding=ROUND_HALF_UP)
        t = (line * Decimal(str(it.get("tax_rate", 0))) / Decimal(100)).quantize(TWO, rounding=ROUND_HALF_UP)
        sub += line
        tax += t
    return sub.quantize(TWO), tax.quantize(TWO), (sub + tax).quantize(TWO)


def _load(db: Session, tenant_id: int, oid: int) -> SalesOrder:
    so = db.query(SalesOrder).options(joinedload(SalesOrder.items), joinedload(SalesOrder.customer)).filter(
        SalesOrder.id == oid, SalesOrder.tenant_id == tenant_id
    ).first()
    if not so:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")
    return so


@router.post("/", response_model=SalesOrderRead, status_code=status.HTTP_201_CREATED)
def create_sales_order(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    cust = db.query(Customer).filter(
        Customer.id == payload.customer_id, Customer.tenant_id == current_user.tenant_id
    ).first()
    if not cust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    existing = db.query(SalesOrder).filter(
        SalesOrder.tenant_id == current_user.tenant_id, SalesOrder.order_number == payload.order_number
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order number already exists")

    items_data = [i.model_dump() for i in payload.items]
    sub, tax, total = _calc(items_data)

    so = SalesOrder(
        tenant_id=current_user.tenant_id,
        customer_id=payload.customer_id,
        quotation_id=payload.quotation_id,
        order_number=payload.order_number,
        order_date=payload.order_date,
        delivery_date=payload.delivery_date,
        subtotal=sub, tax_amount=tax, total=total,
        notes=payload.notes, status=payload.status,
    )
    db.add(so)
    db.flush()

    for it in items_data:
        qty = Decimal(str(it["quantity"]))
        price = Decimal(str(it["unit_price"]))
        amt = (qty * price).quantize(TWO, rounding=ROUND_HALF_UP)
        db.add(SalesOrderItem(
            sales_order_id=so.id, description=it["description"],
            quantity=it["quantity"], unit_price=it["unit_price"],
            tax_rate=it.get("tax_rate", 0), amount=amt,
        ))
    db.commit()
    return _load(db, current_user.tenant_id, so.id)


@router.get("/", response_model=list[SalesOrderRead])
def list_sales_orders(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(SalesOrder).options(joinedload(SalesOrder.items), joinedload(SalesOrder.customer)).filter(
        SalesOrder.tenant_id == current_user.tenant_id
    )
    if status_filter:
        q = q.filter(SalesOrder.status == status_filter)
    return q.order_by(SalesOrder.created_at.desc()).all()


@router.get("/{oid}", response_model=SalesOrderRead)
def get_sales_order(oid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _load(db, current_user.tenant_id, oid)


@router.put("/{oid}", response_model=SalesOrderRead)
def update_sales_order(
    oid: int,
    payload: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    so = _load(db, current_user.tenant_id, oid)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(so, f, v)
    db.commit()
    return _load(db, current_user.tenant_id, oid)


@router.delete("/{oid}")
def delete_sales_order(
    oid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    so = _load(db, current_user.tenant_id, oid)
    db.delete(so)
    db.commit()
    return {"message": "Sales order deleted"}
