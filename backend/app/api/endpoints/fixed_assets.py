from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.accounting import FixedAsset
from backend.app.models.user import User
from backend.app.schemas.accounting import FixedAssetCreate, FixedAssetRead, FixedAssetUpdate

router = APIRouter()


def _compute(asset: FixedAsset) -> FixedAssetRead:
    cost = Decimal(str(asset.purchase_cost or 0))
    salvage = Decimal(str(asset.salvage_value or 0))
    years = asset.useful_life_years or 1
    annual = ((cost - salvage) / Decimal(years)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    nbv = (cost - Decimal(str(asset.accumulated_depreciation or 0))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    data = {
        "id": asset.id, "tenant_id": asset.tenant_id, "asset_code": asset.asset_code,
        "name": asset.name, "category": asset.category,
        "purchase_date": asset.purchase_date, "purchase_cost": float(cost),
        "salvage_value": float(salvage), "useful_life_years": asset.useful_life_years,
        "depreciation_method": asset.depreciation_method,
        "accumulated_depreciation": float(asset.accumulated_depreciation or 0),
        "status": asset.status, "notes": asset.notes, "created_at": asset.created_at,
        "net_book_value": float(nbv), "annual_depreciation": float(annual),
    }
    return FixedAssetRead(**data)


def _get(db: Session, tid: int, aid: int) -> FixedAsset:
    a = db.query(FixedAsset).filter(FixedAsset.id == aid, FixedAsset.tenant_id == tid).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return a


@router.post("/", response_model=FixedAssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(payload: FixedAssetCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_write)):
    existing = db.query(FixedAsset).filter(
        FixedAsset.tenant_id == current_user.tenant_id,
        FixedAsset.asset_code == payload.asset_code
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset code already exists")
    a = FixedAsset(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(a); db.commit(); db.refresh(a)
    return _compute(a)


@router.get("/", response_model=list[FixedAssetRead])
def list_assets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assets = db.query(FixedAsset).filter(
        FixedAsset.tenant_id == current_user.tenant_id
    ).order_by(FixedAsset.asset_code).all()
    return [_compute(a) for a in assets]


@router.put("/{aid}", response_model=FixedAssetRead)
def update_asset(aid: int, payload: FixedAssetUpdate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_write)):
    a = _get(db, current_user.tenant_id, aid)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, f, v)
    db.commit(); db.refresh(a)
    return _compute(a)


@router.post("/{aid}/depreciate", response_model=FixedAssetRead)
def run_depreciation(aid: int, db: Session = Depends(get_db),
                     current_user: User = Depends(require_write)):
    """Apply one year of straight-line depreciation."""
    a = _get(db, current_user.tenant_id, aid)
    cost = Decimal(str(a.purchase_cost or 0))
    salvage = Decimal(str(a.salvage_value or 0))
    years = a.useful_life_years or 1
    annual = (cost - salvage) / Decimal(years)
    new_accum = Decimal(str(a.accumulated_depreciation or 0)) + annual
    max_depr = cost - salvage
    if new_accum > max_depr:
        new_accum = max_depr
    a.accumulated_depreciation = float(new_accum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    db.commit(); db.refresh(a)
    return _compute(a)


@router.delete("/{aid}")
def delete_asset(aid: int, db: Session = Depends(get_db),
                 current_user: User = Depends(require_write)):
    a = _get(db, current_user.tenant_id, aid)
    db.delete(a); db.commit()
    return {"message": "Asset deleted"}
