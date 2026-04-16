from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.crm import Lead
from backend.app.models.user import User
from backend.app.schemas.crm import LeadCreate, LeadRead, LeadUpdate

router = APIRouter()


def _get_or_404(db: Session, tenant_id: int, lead_id: int) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == tenant_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.post("/", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    lead = Lead(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/", response_model=list[LeadRead])
def list_leads(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Lead).filter(Lead.tenant_id == current_user.tenant_id)
    if status_filter:
        q = q.filter(Lead.status == status_filter)
    return q.order_by(Lead.created_at.desc()).all()


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_or_404(db, current_user.tenant_id, lead_id)


@router.put("/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    lead = _get_or_404(db, current_user.tenant_id, lead_id)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(lead, f, v)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    lead = _get_or_404(db, current_user.tenant_id, lead_id)
    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted"}
