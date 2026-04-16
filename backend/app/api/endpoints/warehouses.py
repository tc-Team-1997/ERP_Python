from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.inventory import Warehouse
from backend.app.models.user import User
from backend.app.schemas.inventory import WarehouseCreate, WarehouseRead, WarehouseUpdate

router = APIRouter()


def _get(db: Session, tid: int, wid: int) -> Warehouse:
    w = db.query(Warehouse).filter(Warehouse.id == wid, Warehouse.tenant_id == tid).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return w


@router.post("/", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(require_write)):
    existing = db.query(Warehouse).filter(
        Warehouse.tenant_id == current_user.tenant_id, Warehouse.code == payload.code
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse code already exists")
    w = Warehouse(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(w); db.commit(); db.refresh(w)
    return w


@router.get("/", response_model=list[WarehouseRead])
def list_warehouses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Warehouse).filter(Warehouse.tenant_id == current_user.tenant_id).order_by(Warehouse.name).all()


@router.put("/{wid}", response_model=WarehouseRead)
def update_warehouse(wid: int, payload: WarehouseUpdate, db: Session = Depends(get_db),
                     current_user: User = Depends(require_write)):
    w = _get(db, current_user.tenant_id, wid)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(w, f, v)
    db.commit(); db.refresh(w)
    return w


@router.delete("/{wid}")
def delete_warehouse(wid: int, db: Session = Depends(get_db), current_user: User = Depends(require_write)):
    w = _get(db, current_user.tenant_id, wid)
    db.delete(w); db.commit()
    return {"message": "Warehouse deleted"}
