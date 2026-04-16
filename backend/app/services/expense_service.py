from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from backend.app.models.expense import Expense, ExpenseCategory

TWO = Decimal("0.01")


def get_expense_report(db: Session, tenant_id: int, month: int | None, year: int | None) -> dict:
    """Generate an expense report grouped by category for a given period."""
    query = (
        db.query(
            ExpenseCategory.name.label("category_name"),
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("expense_count"),
        )
        .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id)
        .filter(Expense.tenant_id == tenant_id)
    )

    if year:
        query = query.filter(extract("year", Expense.expense_date) == year)
    if month:
        query = query.filter(extract("month", Expense.expense_date) == month)

    rows = query.group_by(ExpenseCategory.name).order_by(func.sum(Expense.amount).desc()).all()

    by_category = []
    grand_total = Decimal(0)
    for row in rows:
        amt = Decimal(str(row.total_amount or 0)).quantize(TWO, rounding=ROUND_HALF_UP)
        by_category.append({
            "category_name": row.category_name,
            "total_amount": float(amt),
            "expense_count": row.expense_count,
        })
        grand_total += amt

    if month and year:
        period = f"{month:02d}/{year}"
    elif year:
        period = str(year)
    else:
        period = "All time"

    return {
        "period": period,
        "total": float(grand_total.quantize(TWO)),
        "by_category": by_category,
    }
