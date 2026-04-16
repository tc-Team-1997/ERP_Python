from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_admin_or_manager, require_write
from backend.app.db.session import get_db
from backend.app.models.procurement import PurchaseRequisition, PurchaseRequisitionItem
from backend.app.models.user import User
from backend.app.schemas.procurement import PRCreate, PRRead, PRUpdate

router = APIRouter()


def _load(db: Session, tid: int, pid: int) -> PurchaseRequisition:
    pr = db.query(PurchaseRequisition).options(
        joinedload(PurchaseRequisition.items)
    ).filter(PurchaseRequisition.id == pid, PurchaseRequisition.tenant_id == tid).first()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    return pr


@router.post("/", response_model=PRRead, status_code=status.HTTP_201_CREATED)
def create_pr(payload: PRCreate, db: Session = Depends(get_db),
              current_user: User = Depends(require_write)):
    existing = db.query(PurchaseRequisition).filter(
        PurchaseRequisition.tenant_id == current_user.tenant_id,
        PurchaseRequisition.pr_number == payload.pr_number
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PR number already exists")

    pr = PurchaseRequisition(
        tenant_id=current_user.tenant_id,
        requested_by=current_user.id,
        pr_number=payload.pr_number,
        pr_date=payload.pr_date,
        department=payload.department,
        reason=payload.reason,
        status="pending",
    )
    db.add(pr)
    db.flush()

    for it in payload.items:
        db.add(PurchaseRequisitionItem(
            pr_id=pr.id, item_id=it.item_id,
            description=it.description, quantity=it.quantity,
            estimated_price=it.estimated_price,
        ))
    db.commit()
    return _load(db, current_user.tenant_id, pr.id)


@router.get("/", response_model=list[PRRead])
def list_prs(status_filter: str | None = None,
             db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(PurchaseRequisition).options(joinedload(PurchaseRequisition.items)).filter(
        PurchaseRequisition.tenant_id == current_user.tenant_id
    )
    if status_filter:
        q = q.filter(PurchaseRequisition.status == status_filter)
    return q.order_by(PurchaseRequisition.created_at.desc()).all()


@router.get("/{pid}", response_model=PRRead)
def get_pr(pid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _load(db, current_user.tenant_id, pid)


@router.put("/{pid}/approve", response_model=PRRead)
def approve_pr(pid: int, db: Session = Depends(get_db),
               current_user: User = Depends(require_admin_or_manager)):
    pr = _load(db, current_user.tenant_id, pid)
    pr.status = "approved"
    pr.approved_by = current_user.id
    pr.approved_at = datetime.now(timezone.utc)
    db.commit()
    return _load(db, current_user.tenant_id, pid)


@router.put("/{pid}/reject", response_model=PRRead)
def reject_pr(pid: int, payload: PRUpdate, db: Session = Depends(get_db),
              current_user: User = Depends(require_admin_or_manager)):
    pr = _load(db, current_user.tenant_id, pid)
    pr.status = "rejected"
    pr.approver_comment = payload.approver_comment
    pr.approved_by = current_user.id
    pr.approved_at = datetime.now(timezone.utc)
    db.commit()
    return _load(db, current_user.tenant_id, pid)


@router.delete("/{pid}")
def delete_pr(pid: int, db: Session = Depends(get_db), current_user: User = Depends(require_write)):
    pr = _load(db, current_user.tenant_id, pid)
    db.delete(pr); db.commit()
    return {"message": "PR deleted"}
