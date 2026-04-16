import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.expense import Expense, ExpenseCategory
from backend.app.models.user import User
from backend.app.schemas.expense import (
    ExpenseCategoryCreate,
    ExpenseCategoryRead,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseRead,
    ExpenseReport,
    ExpenseUpdate,
)
from backend.app.services.expense_service import get_expense_report

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "receipts")


# ---- Expense Categories ----

@router.post("/categories/", response_model=ExpenseCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.tenant_id == current_user.tenant_id, ExpenseCategory.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")

    category = ExpenseCategory(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/categories/", response_model=list[ExpenseCategoryRead])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.tenant_id == current_user.tenant_id)
        .order_by(ExpenseCategory.name)
        .all()
    )


@router.put("/categories/{category_id}", response_model=ExpenseCategoryRead)
def update_category(
    category_id: int,
    payload: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id, ExpenseCategory.tenant_id == current_user.tenant_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    category = db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id, ExpenseCategory.tenant_id == current_user.tenant_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


# ---- Expenses ----

@router.post("/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = db.query(ExpenseCategory).filter(ExpenseCategory.id == payload.category_id, ExpenseCategory.tenant_id == current_user.tenant_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    expense = Expense(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return db.query(Expense).options(joinedload(Expense.category)).filter(Expense.id == expense.id).first()


@router.get("/", response_model=list[ExpenseRead])
def list_expenses(
    category_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import extract

    query = (
        db.query(Expense)
        .options(joinedload(Expense.category))
        .filter(Expense.tenant_id == current_user.tenant_id)
    )
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if year:
        query = query.filter(extract("year", Expense.expense_date) == year)
    if month:
        query = query.filter(extract("month", Expense.expense_date) == month)
    return query.order_by(Expense.expense_date.desc()).all()


@router.get("/report", response_model=ExpenseReport)
def expense_report(
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_expense_report(db, current_user.tenant_id, month, year)


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = (
        db.query(Expense)
        .options(joinedload(Expense.category))
        .filter(Expense.id == expense_id, Expense.tenant_id == current_user.tenant_id)
        .first()
    )
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.tenant_id == current_user.tenant_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    db.add(expense)
    db.commit()
    return db.query(Expense).options(joinedload(Expense.category)).filter(Expense.id == expense.id).first()


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.tenant_id == current_user.tenant_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}


@router.post("/{expense_id}/receipt", response_model=ExpenseRead)
def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.tenant_id == current_user.tenant_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    safe_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, safe_name)

    with open(path, "wb") as f:
        f.write(file.file.read())

    expense.receipt_filename = file.filename
    expense.receipt_path = path
    db.add(expense)
    db.commit()
    return db.query(Expense).options(joinedload(Expense.category)).filter(Expense.id == expense.id).first()
