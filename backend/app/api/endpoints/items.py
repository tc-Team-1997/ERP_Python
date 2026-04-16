from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.inventory import Item
from backend.app.models.user import User
from backend.app.schemas.inventory import ItemCreate, ItemRead, ItemUpdate, StockSummary

router = APIRouter()


def _get(db: Session, tid: int, iid: int) -> Item:
    it = db.query(Item).filter(Item.id == iid, Item.tenant_id == tid).first()
    if not it:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return it


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db),
                current_user: User = Depends(require_write)):
    existing = db.query(Item).filter(
        Item.tenant_id == current_user.tenant_id, Item.sku == payload.sku
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SKU already exists")
    it = Item(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(it); db.commit(); db.refresh(it)
    return it


@router.get("/", response_model=list[ItemRead])
def list_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Item).filter(Item.tenant_id == current_user.tenant_id).order_by(Item.name).all()


@router.get("/low-stock", response_model=list[StockSummary])
def low_stock_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Item).filter(
        Item.tenant_id == current_user.tenant_id,
        Item.current_stock <= Item.reorder_level,
    ).all()
    return [
        StockSummary(
            item_id=it.id, sku=it.sku, name=it.name,
            current_stock=it.current_stock, reorder_level=it.reorder_level,
            needs_reorder=True,
        ) for it in items
    ]


@router.get("/{iid}", response_model=ItemRead)
def get_item(iid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get(db, current_user.tenant_id, iid)


@router.put("/{iid}", response_model=ItemRead)
def update_item(iid: int, payload: ItemUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(require_write)):
    it = _get(db, current_user.tenant_id, iid)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(it, f, v)
    db.commit(); db.refresh(it)
    return it


@router.delete("/{iid}")
def delete_item(iid: int, db: Session = Depends(get_db), current_user: User = Depends(require_write)):
    it = _get(db, current_user.tenant_id, iid)
    db.delete(it); db.commit()
    return {"message": "Item deleted"}
