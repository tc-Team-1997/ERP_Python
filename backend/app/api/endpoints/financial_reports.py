from datetime import date as date_cls
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.accounting import ChartOfAccounts, JournalEntry, JournalLine
from backend.app.models.user import User
from backend.app.schemas.accounting import (
    BalanceSheet, BalanceSheetRow, PnLRow, ProfitAndLoss,
    TrialBalance, TrialBalanceRow,
)

router = APIRouter()


def _account_balance(db: Session, tenant_id: int, account_id: int,
                     start_date: date_cls | None = None,
                     end_date: date_cls | None = None) -> tuple[Decimal, Decimal]:
    """Return (total_debit, total_credit) for an account from posted entries."""
    q = db.query(
        func.coalesce(func.sum(JournalLine.debit), 0).label("d"),
        func.coalesce(func.sum(JournalLine.credit), 0).label("c"),
    ).join(JournalEntry, JournalLine.entry_id == JournalEntry.id).filter(
        JournalEntry.tenant_id == tenant_id,
        JournalEntry.status == "posted",
        JournalLine.account_id == account_id,
    )
    if start_date:
        q = q.filter(JournalEntry.entry_date >= start_date)
    if end_date:
        q = q.filter(JournalEntry.entry_date <= end_date)
    row = q.first()
    return Decimal(str(row.d)), Decimal(str(row.c))


@router.get("/trial-balance", response_model=TrialBalance)
def trial_balance(as_of: date_cls, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    accounts = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.tenant_id == current_user.tenant_id,
        ChartOfAccounts.is_active.is_(True),
    ).order_by(ChartOfAccounts.code).all()

    rows = []
    total_d = Decimal(0); total_c = Decimal(0)
    for acc in accounts:
        d, c = _account_balance(db, current_user.tenant_id, acc.id, end_date=as_of)
        # Net balance: asset/expense — debit normal; liability/equity/income — credit normal
        net = d - c
        debit_amt = float(net) if net > 0 else 0.0
        credit_amt = float(-net) if net < 0 else 0.0
        if debit_amt == 0 and credit_amt == 0:
            continue
        rows.append(TrialBalanceRow(
            account_id=acc.id, code=acc.code, name=acc.name,
            account_type=acc.account_type,
            debit=debit_amt, credit=credit_amt,
        ))
        total_d += Decimal(str(debit_amt))
        total_c += Decimal(str(credit_amt))

    return TrialBalance(
        as_of=as_of, rows=rows,
        total_debit=float(total_d), total_credit=float(total_c),
    )


@router.get("/profit-and-loss", response_model=ProfitAndLoss)
def profit_and_loss(period_start: date_cls, period_end: date_cls,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    accounts = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.tenant_id == current_user.tenant_id,
        ChartOfAccounts.account_type.in_(("income", "expense")),
    ).order_by(ChartOfAccounts.code).all()

    income = []; expenses = []
    total_inc = Decimal(0); total_exp = Decimal(0)

    for acc in accounts:
        d, c = _account_balance(db, current_user.tenant_id, acc.id, period_start, period_end)
        if acc.account_type == "income":
            amt = c - d  # income credit normal
            if amt != 0:
                income.append(PnLRow(account_type="income", code=acc.code, name=acc.name, amount=float(amt)))
                total_inc += amt
        else:
            amt = d - c  # expense debit normal
            if amt != 0:
                expenses.append(PnLRow(account_type="expense", code=acc.code, name=acc.name, amount=float(amt)))
                total_exp += amt

    return ProfitAndLoss(
        period_start=period_start, period_end=period_end,
        income=income, expenses=expenses,
        total_income=float(total_inc), total_expenses=float(total_exp),
        net_profit=float(total_inc - total_exp),
    )


@router.get("/balance-sheet", response_model=BalanceSheet)
def balance_sheet(as_of: date_cls, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    accounts = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.tenant_id == current_user.tenant_id,
        ChartOfAccounts.account_type.in_(("asset", "liability", "equity")),
    ).order_by(ChartOfAccounts.code).all()

    assets = []; liabilities = []; equity_rows = []
    ta = Decimal(0); tl = Decimal(0); te = Decimal(0)

    for acc in accounts:
        d, c = _account_balance(db, current_user.tenant_id, acc.id, end_date=as_of)
        if acc.account_type == "asset":
            amt = d - c
            if amt != 0:
                assets.append(BalanceSheetRow(code=acc.code, name=acc.name, amount=float(amt)))
                ta += amt
        elif acc.account_type == "liability":
            amt = c - d
            if amt != 0:
                liabilities.append(BalanceSheetRow(code=acc.code, name=acc.name, amount=float(amt)))
                tl += amt
        else:
            amt = c - d
            if amt != 0:
                equity_rows.append(BalanceSheetRow(code=acc.code, name=acc.name, amount=float(amt)))
                te += amt

    # Compute retained earnings = income - expenses (all time up to as_of)
    inc_accs = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.tenant_id == current_user.tenant_id,
        ChartOfAccounts.account_type.in_(("income", "expense")),
    ).all()
    retained = Decimal(0)
    for a in inc_accs:
        d, c = _account_balance(db, current_user.tenant_id, a.id, end_date=as_of)
        if a.account_type == "income":
            retained += (c - d)
        else:
            retained -= (d - c)

    return BalanceSheet(
        as_of=as_of, assets=assets, liabilities=liabilities, equity=equity_rows,
        total_assets=float(ta), total_liabilities=float(tl),
        total_equity=float(te + retained),
        retained_earnings=float(retained),
    )
