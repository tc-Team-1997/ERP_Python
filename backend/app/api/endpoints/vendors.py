from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.procurement import Vendor
from backend.app.models.user import User
from backend.app.schemas.procurement import VendorCreate, VendorRead, VendorUpdate

router = APIRouter()


def _get(db: Session, tid: int, vid: int) -> Vendor:
    v = db.query(Vendor).filter(Vendor.id == vid, Vendor.tenant_id == tid).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return v


@router.post("/", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(require_write)):
    existing = db.query(Vendor).filter(
        Vendor.tenant_id == current_user.tenant_id, Vendor.code == payload.code
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor code already exists")
    v = Vendor(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(v); db.commit(); db.refresh(v)
    return v


@router.get("/", response_model=list[VendorRead])
def list_vendors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Vendor).filter(Vendor.tenant_id == current_user.tenant_id).order_by(Vendor.name).all()


@router.put("/{vid}", response_model=VendorRead)
def update_vendor(vid: int, payload: VendorUpdate, db: Session = Depends(get_db),
                  current_user: User = Depends(require_write)):
    v = _get(db, current_user.tenant_id, vid)
    for f, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, f, val)
    db.commit(); db.refresh(v)
    return v


@router.delete("/{vid}")
def delete_vendor(vid: int, db: Session = Depends(get_db), current_user: User = Depends(require_write)):
    v = _get(db, current_user.tenant_id, vid)
    db.delete(v); db.commit()
    return {"message": "Vendor deleted"}
