from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_admin_or_manager, require_write
from backend.app.db.session import get_db
from backend.app.models.procurement import PurchaseOrder, PurchaseOrderItem, PurchaseRequisition, Vendor
from backend.app.models.user import User
from backend.app.schemas.procurement import POCreate, PORead, POUpdate

router = APIRouter()
TWO = Decimal("0.01")


def _calc(items: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
    sub = Decimal(0); tax = Decimal(0)
    for it in items:
        qty = Decimal(str(it["quantity"]))
        price = Decimal(str(it["unit_price"]))
        line = (qty * price).quantize(TWO, rounding=ROUND_HALF_UP)
        t = (line * Decimal(str(it.get("tax_rate", 0))) / Decimal(100)).quantize(TWO, rounding=ROUND_HALF_UP)
        sub += line; tax += t
    return sub.quantize(TWO), tax.quantize(TWO), (sub + tax).quantize(TWO)


def _load(db: Session, tid: int, pid: int) -> PurchaseOrder:
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.items), joinedload(PurchaseOrder.vendor)
    ).filter(PurchaseOrder.id == pid, PurchaseOrder.tenant_id == tid).first()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")
    return po


@router.post("/", response_model=PORead, status_code=status.HTTP_201_CREATED)
def create_po(payload: POCreate, db: Session = Depends(get_db),
              current_user: User = Depends(require_write)):
    vendor = db.query(Vendor).filter(
        Vendor.id == payload.vendor_id, Vendor.tenant_id == current_user.tenant_id
    ).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    existing = db.query(PurchaseOrder).filter(
        PurchaseOrder.tenant_id == current_user.tenant_id,
        PurchaseOrder.po_number == payload.po_number
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PO number already exists")

    if payload.pr_id:
        pr = db.query(PurchaseRequisition).filter(
            PurchaseRequisition.id == payload.pr_id,
            PurchaseRequisition.tenant_id == current_user.tenant_id
        ).first()
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
        if pr.status != "approved":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="PR must be approved before converting to PO")

    items_data = [i.model_dump() for i in payload.items]
    sub, tax, total = _calc(items_data)

    po = PurchaseOrder(
        tenant_id=current_user.tenant_id,
        vendor_id=payload.vendor_id, pr_id=payload.pr_id,
        po_number=payload.po_number, po_date=payload.po_date,
        expected_delivery=payload.expected_delivery,
        subtotal=sub, tax_amount=tax, total=total,
        status=payload.status, notes=payload.notes,
    )
    db.add(po); db.flush()

    for it in items_data:
        qty = Decimal(str(it["quantity"])); price = Decimal(str(it["unit_price"]))
        amt = (qty * price).quantize(TWO, rounding=ROUND_HALF_UP)
        db.add(PurchaseOrderItem(
            po_id=po.id, item_id=it.get("item_id"),
            description=it["description"], quantity=it["quantity"],
            unit_price=it["unit_price"], tax_rate=it.get("tax_rate", 0),
            amount=amt,
        ))

    # If PR was linked, mark it converted
    if payload.pr_id:
        pr = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == payload.pr_id).first()
        if pr:
            pr.status = "converted"

    db.commit()
    return _load(db, current_user.tenant_id, po.id)


@router.get("/", response_model=list[PORead])
def list_pos(status_filter: str | None = None,
             db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.items), joinedload(PurchaseOrder.vendor)
    ).filter(PurchaseOrder.tenant_id == current_user.tenant_id)
    if status_filter:
        q = q.filter(PurchaseOrder.status == status_filter)
    return q.order_by(PurchaseOrder.created_at.desc()).all()


@router.get("/{pid}", response_model=PORead)
def get_po(pid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _load(db, current_user.tenant_id, pid)


@router.put("/{pid}/approve", response_model=PORead)
def approve_po(pid: int, db: Session = Depends(get_db),
               current_user: User = Depends(require_admin_or_manager)):
    po = _load(db, current_user.tenant_id, pid)
    po.status = "approved"
    po.approved_by = current_user.id
    po.approved_at = datetime.now(timezone.utc)
    db.commit()
    return _load(db, current_user.tenant_id, pid)


@router.put("/{pid}/reject", response_model=PORead)
def reject_po(pid: int, payload: POUpdate, db: Session = Depends(get_db),
              current_user: User = Depends(require_admin_or_manager)):
    po = _load(db, current_user.tenant_id, pid)
    po.status = "rejected"
    po.approver_comment = payload.approver_comment
    db.commit()
    return _load(db, current_user.tenant_id, pid)


@router.put("/{pid}", response_model=PORead)
def update_po(pid: int, payload: POUpdate, db: Session = Depends(get_db),
              current_user: User = Depends(require_write)):
    po = _load(db, current_user.tenant_id, pid)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(po, f, v)
    db.commit()
    return _load(db, current_user.tenant_id, pid)


@router.delete("/{pid}")
def delete_po(pid: int, db: Session = Depends(get_db), current_user: User = Depends(require_write)):
    po = _load(db, current_user.tenant_id, pid)
    db.delete(po); db.commit()
    return {"message": "PO deleted"}
