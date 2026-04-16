from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.inventory import Item, StockMovement
from backend.app.models.procurement import (
    GoodsReceiptNote, GRNItem, PurchaseOrder, PurchaseOrderItem,
)
from backend.app.models.user import User
from backend.app.schemas.procurement import GRNCreate, GRNRead

router = APIRouter()


def _load(db: Session, tid: int, gid: int) -> GoodsReceiptNote:
    g = db.query(GoodsReceiptNote).options(
        joinedload(GoodsReceiptNote.items), joinedload(GoodsReceiptNote.warehouse)
    ).filter(GoodsReceiptNote.id == gid, GoodsReceiptNote.tenant_id == tid).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GRN not found")
    return g


@router.post("/", response_model=GRNRead, status_code=status.HTTP_201_CREATED)
def create_grn(payload: GRNCreate, db: Session = Depends(get_db),
               current_user: User = Depends(require_write)):
    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == payload.po_id, PurchaseOrder.tenant_id == current_user.tenant_id
    ).first()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")
    if po.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="PO must be approved before creating GRN")

    existing = db.query(GoodsReceiptNote).filter(
        GoodsReceiptNote.tenant_id == current_user.tenant_id,
        GoodsReceiptNote.grn_number == payload.grn_number
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GRN number already exists")

    grn = GoodsReceiptNote(
        tenant_id=current_user.tenant_id,
        po_id=payload.po_id,
        warehouse_id=payload.warehouse_id,
        grn_number=payload.grn_number,
        grn_date=payload.grn_date,
        notes=payload.notes,
        status=payload.status,
    )
    db.add(grn); db.flush()

    all_received = True
    for it in payload.items:
        db.add(GRNItem(
            grn_id=grn.id, po_item_id=it.po_item_id, item_id=it.item_id,
            description=it.description, received_quantity=it.received_quantity,
            rejected_quantity=it.rejected_quantity, remarks=it.remarks,
        ))
        # Update PO item received_quantity
        if it.po_item_id:
            poi = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == it.po_item_id).first()
            if poi:
                poi.received_quantity = (poi.received_quantity or 0) + it.received_quantity
                if poi.received_quantity < poi.quantity:
                    all_received = False

        # Update item stock + create stock movement if warehouse given
        if it.item_id and it.received_quantity > 0 and payload.warehouse_id:
            item_row = db.query(Item).filter(
                Item.id == it.item_id, Item.tenant_id == current_user.tenant_id
            ).first()
            if item_row:
                item_row.current_stock = (item_row.current_stock or 0) + it.received_quantity
                db.add(StockMovement(
                    tenant_id=current_user.tenant_id,
                    item_id=it.item_id,
                    warehouse_id=payload.warehouse_id,
                    movement_type="in",
                    quantity=it.received_quantity,
                    reference=f"GRN-{payload.grn_number}",
                    notes=f"From PO {po.po_number}",
                    movement_date=payload.grn_date,
                ))

    # Update PO status if everything received
    if all_received:
        po.status = "received"

    db.commit()
    return _load(db, current_user.tenant_id, grn.id)


@router.get("/", response_model=list[GRNRead])
def list_grns(po_id: int | None = None,
              db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(GoodsReceiptNote).options(
        joinedload(GoodsReceiptNote.items), joinedload(GoodsReceiptNote.warehouse)
    ).filter(GoodsReceiptNote.tenant_id == current_user.tenant_id)
    if po_id:
        q = q.filter(GoodsReceiptNote.po_id == po_id)
    return q.order_by(GoodsReceiptNote.created_at.desc()).all()


@router.get("/{gid}", response_model=GRNRead)
def get_grn(gid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _load(db, current_user.tenant_id, gid)
