from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.crm import Quotation, QuotationItem
from backend.app.models.customer import Customer
from backend.app.models.user import User
from backend.app.schemas.crm import QuotationCreate, QuotationRead, QuotationUpdate

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


def _load(db: Session, tenant_id: int, qid: int) -> Quotation:
    q = db.query(Quotation).options(joinedload(Quotation.items), joinedload(Quotation.customer)).filter(
        Quotation.id == qid, Quotation.tenant_id == tenant_id
    ).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quotation not found")
    return q


@router.post("/", response_model=QuotationRead, status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    cust = db.query(Customer).filter(
        Customer.id == payload.customer_id, Customer.tenant_id == current_user.tenant_id
    ).first()
    if not cust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    existing = db.query(Quotation).filter(
        Quotation.tenant_id == current_user.tenant_id, Quotation.quote_number == payload.quote_number
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quote number already exists")

    items_data = [i.model_dump() for i in payload.items]
    sub, tax, total = _calc(items_data)

    quote = Quotation(
        tenant_id=current_user.tenant_id,
        customer_id=payload.customer_id,
        quote_number=payload.quote_number,
        quote_date=payload.quote_date,
        valid_until=payload.valid_until,
        subtotal=sub, tax_amount=tax, total=total,
        notes=payload.notes, status=payload.status,
    )
    db.add(quote)
    db.flush()

    for it in items_data:
        qty = Decimal(str(it["quantity"]))
        price = Decimal(str(it["unit_price"]))
        amt = (qty * price).quantize(TWO, rounding=ROUND_HALF_UP)
        db.add(QuotationItem(
            quotation_id=quote.id, description=it["description"],
            quantity=it["quantity"], unit_price=it["unit_price"],
            tax_rate=it.get("tax_rate", 0), amount=amt,
        ))
    db.commit()
    return _load(db, current_user.tenant_id, quote.id)


@router.get("/", response_model=list[QuotationRead])
def list_quotations(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Quotation).options(joinedload(Quotation.items), joinedload(Quotation.customer)).filter(
        Quotation.tenant_id == current_user.tenant_id
    )
    if status_filter:
        q = q.filter(Quotation.status == status_filter)
    return q.order_by(Quotation.created_at.desc()).all()


@router.get("/{qid}", response_model=QuotationRead)
def get_quotation(qid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _load(db, current_user.tenant_id, qid)


@router.put("/{qid}", response_model=QuotationRead)
def update_quotation(
    qid: int,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    quote = _load(db, current_user.tenant_id, qid)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(quote, f, v)
    db.commit()
    return _load(db, current_user.tenant_id, qid)


@router.delete("/{qid}")
def delete_quotation(
    qid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    quote = _load(db, current_user.tenant_id, qid)
    db.delete(quote)
    db.commit()
    return {"message": "Quotation deleted"}
