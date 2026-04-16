from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.accounting import ChartOfAccounts
from backend.app.models.user import User
from backend.app.schemas.accounting import AccountCreate, AccountRead, AccountUpdate

router = APIRouter()


def _get(db: Session, tid: int, aid: int) -> ChartOfAccounts:
    a = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.id == aid, ChartOfAccounts.tenant_id == tid
    ).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return a


@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(require_write)):
    existing = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.tenant_id == current_user.tenant_id,
        ChartOfAccounts.code == payload.code
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account code already exists")
    if payload.parent_id:
        parent = db.query(ChartOfAccounts).filter(
            ChartOfAccounts.id == payload.parent_id,
            ChartOfAccounts.tenant_id == current_user.tenant_id
        ).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent account not found")
    a = ChartOfAccounts(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(a); db.commit(); db.refresh(a)
    return a


@router.get("/", response_model=list[AccountRead])
def list_accounts(account_type: str | None = None,
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(ChartOfAccounts).filter(ChartOfAccounts.tenant_id == current_user.tenant_id)
    if account_type:
        q = q.filter(ChartOfAccounts.account_type == account_type)
    return q.order_by(ChartOfAccounts.code).all()


@router.put("/{aid}", response_model=AccountRead)
def update_account(aid: int, payload: AccountUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(require_write)):
    a = _get(db, current_user.tenant_id, aid)
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, f, v)
    db.commit(); db.refresh(a)
    return a


@router.delete("/{aid}")
def delete_account(aid: int, db: Session = Depends(get_db),
                   current_user: User = Depends(require_write)):
    a = _get(db, current_user.tenant_id, aid)
    if a.journal_lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot delete account with journal activity")
    db.delete(a); db.commit()
    return {"message": "Account deleted"}


@router.post("/seed-default", response_model=list[AccountRead])
def seed_default_coa(db: Session = Depends(get_db),
                     current_user: User = Depends(require_write)):
    """Create a standard chart of accounts if none exist."""
    existing = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.tenant_id == current_user.tenant_id
    ).count()
    if existing > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Accounts already exist for this tenant")
    defaults = [
        ("1000", "Cash in Hand", "asset"),
        ("1010", "Bank Account", "asset"),
        ("1100", "Accounts Receivable", "asset"),
        ("1200", "Inventory", "asset"),
        ("1500", "Fixed Assets", "asset"),
        ("1510", "Accumulated Depreciation", "asset"),
        ("2000", "Accounts Payable", "liability"),
        ("2100", "GST Payable", "liability"),
        ("2200", "Salaries Payable", "liability"),
        ("3000", "Owner's Equity", "equity"),
        ("3100", "Retained Earnings", "equity"),
        ("4000", "Sales Revenue", "income"),
        ("4100", "Service Revenue", "income"),
        ("5000", "Cost of Goods Sold", "expense"),
        ("5100", "Salaries Expense", "expense"),
        ("5200", "Rent Expense", "expense"),
        ("5300", "Utilities Expense", "expense"),
        ("5400", "Office Supplies", "expense"),
        ("5500", "Depreciation Expense", "expense"),
        ("5900", "Misc. Expense", "expense"),
    ]
    created = []
    for code, name, at in defaults:
        a = ChartOfAccounts(
            tenant_id=current_user.tenant_id, code=code, name=name, account_type=at
        )
        db.add(a)
        created.append(a)
    db.commit()
    for a in created:
        db.refresh(a)
    return created
