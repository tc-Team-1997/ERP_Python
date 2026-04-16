from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Expense Category ---

class ExpenseCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class ExpenseCategoryRead(ExpenseCategoryBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ExpenseCategoryMini(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# --- Expense ---

class ExpenseBase(BaseModel):
    category_id: int
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    amount: float = Field(gt=0)
    expense_date: date


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    amount: float | None = Field(default=None, gt=0)
    expense_date: date | None = None


class ExpenseRead(ExpenseBase):
    id: int
    tenant_id: int
    receipt_filename: str | None = None
    created_at: datetime | None = None
    category: ExpenseCategoryMini | None = None

    model_config = ConfigDict(from_attributes=True)


class ExpenseReportRow(BaseModel):
    category_name: str
    total_amount: float
    expense_count: int


class ExpenseReport(BaseModel):
    period: str
    total: float
    by_category: list[ExpenseReportRow]
