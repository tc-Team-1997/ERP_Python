from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.accounting import BankAccount, BankTransaction
from backend.app.models.user import User
from backend.app.schemas.accounting import (
    BankAccountCreate, BankAccountRead, BankTxnCreate, BankTxnRead,
)

router = APIRouter()


def _get_account(db: Session, tid: int, aid: int) -> BankAccount:
    a = db.query(BankAccount).filter(BankAccount.id == aid, BankAccount.tenant_id == tid).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")
    return a


def _balance(db: Session, acc: BankAccount) -> float:
    totals = db.query(
        func.coalesce(func.sum(BankTransaction.deposit), 0).label("d"),
        func.coalesce(func.sum(BankTransaction.withdrawal), 0).label("w"),
    ).filter(BankTransaction.bank_account_id == acc.id).first()
    opening = Decimal(str(acc.opening_balance or 0))
    return float(opening + Decimal(str(totals.d)) - Decimal(str(totals.w)))


# ---- Bank Accounts ----
@router.post("/accounts/", response_model=BankAccountRead, status_code=status.HTTP_201_CREATED)
def create_bank_account(payload: BankAccountCreate, db: Session = Depends(get_db),
                        current_user: User = Depends(require_write)):
    existing = db.query(BankAccount).filter(
        BankAccount.tenant_id == current_user.tenant_id,
        BankAccount.account_number == payload.account_number
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account number already exists")
    a = BankAccount(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(a); db.commit(); db.refresh(a)
    result = BankAccountRead.model_validate(a)
    result.current_balance = _balance(db, a)
    return result


@router.get("/accounts/", response_model=list[BankAccountRead])
def list_bank_accounts(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    accs = db.query(BankAccount).filter(
        BankAccount.tenant_id == current_user.tenant_id
    ).order_by(BankAccount.bank_name).all()
    out = []
    for a in accs:
        r = BankAccountRead.model_validate(a)
        r.current_balance = _balance(db, a)
        out.append(r)
    return out


# ---- Transactions ----
@router.post("/transactions/", response_model=BankTxnRead, status_code=status.HTTP_201_CREATED)
def create_txn(payload: BankTxnCreate, db: Session = Depends(get_db),
               current_user: User = Depends(require_write)):
    _get_account(db, current_user.tenant_id, payload.bank_account_id)
    t = BankTransaction(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(t); db.commit(); db.refresh(t)
    return t


@router.get("/transactions/", response_model=list[BankTxnRead])
def list_txns(bank_account_id: int | None = None, reconciled: bool | None = None,
              db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(BankTransaction).filter(BankTransaction.tenant_id == current_user.tenant_id)
    if bank_account_id:
        q = q.filter(BankTransaction.bank_account_id == bank_account_id)
    if reconciled is not None:
        q = q.filter(BankTransaction.reconciled == reconciled)
    return q.order_by(BankTransaction.txn_date.desc(), BankTransaction.id.desc()).all()


@router.put("/transactions/{tid}/reconcile", response_model=BankTxnRead)
def reconcile_txn(tid: int, db: Session = Depends(get_db),
                  current_user: User = Depends(require_write)):
    t = db.query(BankTransaction).filter(
        BankTransaction.id == tid, BankTransaction.tenant_id == current_user.tenant_id
    ).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    t.reconciled = True
    t.reconciled_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(t)
    return t


@router.put("/transactions/{tid}/unreconcile", response_model=BankTxnRead)
def unreconcile_txn(tid: int, db: Session = Depends(get_db),
                    current_user: User = Depends(require_write)):
    t = db.query(BankTransaction).filter(
        BankTransaction.id == tid, BankTransaction.tenant_id == current_user.tenant_id
    ).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    t.reconciled = False
    t.reconciled_at = None
    db.commit(); db.refresh(t)
    return t
