from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.crm import Opportunity
from backend.app.models.user import User
from backend.app.schemas.crm import OpportunityCreate, OpportunityRead, OpportunityUpdate

router = APIRouter()


def _get_or_404(db: Session, tenant_id: int, opp_id: int) -> Opportunity:
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id, Opportunity.tenant_id == tenant_id).first()
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opp


@router.post("/", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    opp = Opportunity(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(opp)
    db.commit()
    return db.query(Opportunity).options(joinedload(Opportunity.customer)).filter(Opportunity.id == opp.id).first()


@router.get("/", response_model=list[OpportunityRead])
def list_opportunities(
    stage: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Opportunity).options(joinedload(Opportunity.customer)).filter(
        Opportunity.tenant_id == current_user.tenant_id
    )
    if stage:
        q = q.filter(Opportunity.stage == stage)
    return q.order_by(Opportunity.created_at.desc()).all()


@router.put("/{opp_id}", response_model=OpportunityRead)
def update_opportunity(
    opp_id: int,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    opp = _get_or_404(db, current_user.tenant_id, opp_id)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(opp, f, v)
    db.commit()
    return db.query(Opportunity).options(joinedload(Opportunity.customer)).filter(Opportunity.id == opp.id).first()


@router.delete("/{opp_id}")
def delete_opportunity(
    opp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write),
):
    opp = _get_or_404(db, current_user.tenant_id, opp_id)
    db.delete(opp)
    db.commit()
    return {"message": "Opportunity deleted"}
