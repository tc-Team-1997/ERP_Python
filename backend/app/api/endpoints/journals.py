from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_write
from backend.app.db.session import get_db
from backend.app.models.accounting import ChartOfAccounts, JournalEntry, JournalLine
from backend.app.models.user import User
from backend.app.schemas.accounting import JournalEntryCreate, JournalEntryRead

router = APIRouter()
TWO = Decimal("0.01")


def _load(db: Session, tid: int, eid: int) -> JournalEntry:
    e = db.query(JournalEntry).options(
        joinedload(JournalEntry.lines).joinedload(JournalLine.account)
    ).filter(JournalEntry.id == eid, JournalEntry.tenant_id == tid).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return e


@router.post("/", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(payload: JournalEntryCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_write)):
    existing = db.query(JournalEntry).filter(
        JournalEntry.tenant_id == current_user.tenant_id,
        JournalEntry.entry_number == payload.entry_number
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entry number already exists")

    # Validate all accounts belong to tenant
    account_ids = {l.account_id for l in payload.lines}
    count = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.tenant_id == current_user.tenant_id,
        ChartOfAccounts.id.in_(account_ids)
    ).count()
    if count != len(account_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="One or more accounts not found")

    total_d = Decimal(0); total_c = Decimal(0)
    for l in payload.lines:
        total_d += Decimal(str(l.debit))
        total_c += Decimal(str(l.credit))

    e = JournalEntry(
        tenant_id=current_user.tenant_id,
        entry_number=payload.entry_number,
        entry_date=payload.entry_date,
        reference=payload.reference,
        description=payload.description,
        total_debit=total_d.quantize(TWO, rounding=ROUND_HALF_UP),
        total_credit=total_c.quantize(TWO, rounding=ROUND_HALF_UP),
        status=payload.status,
        created_by=current_user.id,
    )
    db.add(e); db.flush()

    for l in payload.lines:
        db.add(JournalLine(
            entry_id=e.id, account_id=l.account_id,
            debit=l.debit, credit=l.credit, narration=l.narration,
        ))
    db.commit()
    return _load(db, current_user.tenant_id, e.id)


@router.get("/", response_model=list[JournalEntryRead])
def list_entries(status_filter: str | None = None,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    q = db.query(JournalEntry).options(
        joinedload(JournalEntry.lines).joinedload(JournalLine.account)
    ).filter(JournalEntry.tenant_id == current_user.tenant_id)
    if status_filter:
        q = q.filter(JournalEntry.status == status_filter)
    return q.order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc()).all()


@router.get("/{eid}", response_model=JournalEntryRead)
def get_entry(eid: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    return _load(db, current_user.tenant_id, eid)


@router.put("/{eid}/reverse", response_model=JournalEntryRead)
def reverse_entry(eid: int, db: Session = Depends(get_db),
                  current_user: User = Depends(require_write)):
    """Create a reversing entry (swap debits and credits)."""
    original = _load(db, current_user.tenant_id, eid)
    if original.status == "reversed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entry already reversed")

    rev = JournalEntry(
        tenant_id=current_user.tenant_id,
        entry_number=f"{original.entry_number}-REV",
        entry_date=original.entry_date,
        reference=f"Reversal of {original.entry_number}",
        description=f"Auto-reversal of entry #{original.entry_number}",
        total_debit=original.total_credit,
        total_credit=original.total_debit,
        status="posted",
        created_by=current_user.id,
    )
    db.add(rev); db.flush()

    for ln in original.lines:
        db.add(JournalLine(
            entry_id=rev.id, account_id=ln.account_id,
            debit=ln.credit, credit=ln.debit,
            narration=f"Reversal: {ln.narration or ''}",
        ))

    original.status = "reversed"
    db.commit()
    return _load(db, current_user.tenant_id, rev.id)
