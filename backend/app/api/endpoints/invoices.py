from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.customer import Customer
from backend.app.models.invoice import Invoice, InvoiceItem
from backend.app.models.tenant import Tenant
from backend.app.models.user import User
from backend.app.schemas.invoice import InvoiceCreate, InvoiceRead, InvoiceUpdate
from backend.app.services.invoice_service import build_invoice_excel, build_invoice_pdf, calculate_invoice_totals

router = APIRouter()


def _load_invoice(db: Session, tenant_id: int, invoice_id: int) -> Invoice:
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.items), joinedload(Invoice.customer))
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Validate customer belongs to tenant
    customer = db.query(Customer).filter(Customer.id == payload.customer_id, Customer.tenant_id == current_user.tenant_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # Unique invoice number per tenant
    existing = db.query(Invoice).filter(Invoice.tenant_id == current_user.tenant_id, Invoice.invoice_number == payload.invoice_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice number already exists")

    # Calculate totals
    items_data = [item.model_dump() for item in payload.items]
    subtotal, tax_amount, total = calculate_invoice_totals(items_data, payload.discount)

    invoice = Invoice(
        tenant_id=current_user.tenant_id,
        customer_id=payload.customer_id,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount=payload.discount,
        total=total,
        notes=payload.notes,
        status=payload.status,
    )
    db.add(invoice)
    db.flush()

    for item_data in items_data:
        from decimal import Decimal, ROUND_HALF_UP
        qty = Decimal(str(item_data["quantity"]))
        price = Decimal(str(item_data["unit_price"]))
        amount = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        db_item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data["description"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            tax_rate=item_data.get("tax_rate", 0),
            amount=amount,
        )
        db.add(db_item)

    db.commit()
    return _load_invoice(db, current_user.tenant_id, invoice.id)


@router.get("/", response_model=list[InvoiceRead])
def list_invoices(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Invoice)
        .options(joinedload(Invoice.items), joinedload(Invoice.customer))
        .filter(Invoice.tenant_id == current_user.tenant_id)
    )
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    return query.order_by(Invoice.created_at.desc()).all()


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _load_invoice(db, current_user.tenant_id, invoice_id)


@router.put("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    invoice = _load_invoice(db, current_user.tenant_id, invoice_id)

    update_data = payload.model_dump(exclude_unset=True)
    new_items = update_data.pop("items", None)

    for field, value in update_data.items():
        setattr(invoice, field, value)

    if new_items is not None:
        # Replace all items
        for old_item in invoice.items:
            db.delete(old_item)
        db.flush()

        from decimal import Decimal, ROUND_HALF_UP
        for item_data in new_items:
            qty = Decimal(str(item_data["quantity"]))
            price = Decimal(str(item_data["unit_price"]))
            amount = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            db_item = InvoiceItem(
                invoice_id=invoice.id,
                description=item_data["description"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                tax_rate=item_data.get("tax_rate", 0),
                amount=amount,
            )
            db.add(db_item)

        subtotal, tax_amount, total = calculate_invoice_totals(new_items, invoice.discount)
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total = total

    db.add(invoice)
    db.commit()
    return _load_invoice(db, current_user.tenant_id, invoice.id)


@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    invoice = _load_invoice(db, current_user.tenant_id, invoice_id)
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully"}


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invoice = _load_invoice(db, current_user.tenant_id, invoice_id)
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    pdf_buf = build_invoice_pdf(tenant.name if tenant else "Business", invoice)
    filename = f"invoice_{invoice.invoice_number}.pdf"
    return StreamingResponse(pdf_buf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{invoice_id}/excel")
def download_invoice_excel(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invoice = _load_invoice(db, current_user.tenant_id, invoice_id)
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    excel_buf = build_invoice_excel(tenant.name if tenant else "Business", invoice)
    filename = f"invoice_{invoice.invoice_number}.csv"
    return StreamingResponse(excel_buf, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
