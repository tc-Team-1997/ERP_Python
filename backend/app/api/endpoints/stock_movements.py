from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.inventory import Item, StockMovement, Warehouse
from backend.app.models.user import User
from backend.app.schemas.inventory import StockMovementCreate, StockMovementRead

router = APIRouter()


@router.post("/", response_model=StockMovementRead, status_code=status.HTTP_201_CREATED)
def create_movement(payload: StockMovementCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_write)):
    item = db.query(Item).filter(Item.id == payload.item_id, Item.tenant_id == current_user.tenant_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    wh = db.query(Warehouse).filter(
        Warehouse.id == payload.warehouse_id, Warehouse.tenant_id == current_user.tenant_id
    ).first()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    mv = StockMovement(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(mv)

    # Update item stock
    delta = payload.quantity
    if payload.movement_type in ("in",):
        item.current_stock = (item.current_stock or 0) + delta
    elif payload.movement_type in ("out",):
        item.current_stock = (item.current_stock or 0) - delta
        if item.current_stock < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Insufficient stock. Available: {item.current_stock + delta}")
    elif payload.movement_type == "adjustment":
        # adjustment: signed — use quantity as absolute new delta (positive = add, kept simple)
        item.current_stock = (item.current_stock or 0) + delta

    db.commit()
    return db.query(StockMovement).options(
        joinedload(StockMovement.item), joinedload(StockMovement.warehouse)
    ).filter(StockMovement.id == mv.id).first()


@router.get("/", response_model=list[StockMovementRead])
def list_movements(
    item_id: int | None = None,
    warehouse_id: int | None = None,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    q = db.query(StockMovement).options(
        joinedload(StockMovement.item), joinedload(StockMovement.warehouse)
    ).filter(StockMovement.tenant_id == current_user.tenant_id)
    if item_id:
        q = q.filter(StockMovement.item_id == item_id)
    if warehouse_id:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)
    return q.order_by(StockMovement.movement_date.desc(), StockMovement.id.desc()).all()
