from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---- Chart of Accounts ----
class AccountBase(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=150)
    account_type: str = Field(pattern=r"^(asset|liability|equity|income|expense)$")
    parent_id: int | None = None
    description: str | None = None
    is_active: bool = True


class AccountCreate(AccountBase): pass


class AccountUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AccountRead(AccountBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class AccountMini(BaseModel):
    id: int
    code: str
    name: str
    account_type: str
    model_config = ConfigDict(from_attributes=True)


# ---- Journal Entries ----
class JournalLineBase(BaseModel):
    account_id: int
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    narration: str | None = None

    @model_validator(mode="after")
    def only_one_side(self):
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A journal line can have debit OR credit, not both")
        if self.debit == 0 and self.credit == 0:
            raise ValueError("A journal line must have either debit or credit > 0")
        return self


class JournalLineRead(BaseModel):
    id: int
    entry_id: int
    account_id: int
    debit: float
    credit: float
    narration: str | None = None
    account: AccountMini | None = None
    model_config = ConfigDict(from_attributes=True)


class JournalEntryCreate(BaseModel):
    entry_number: str = Field(min_length=1, max_length=50)
    entry_date: date
    reference: str | None = None
    description: str | None = None
    status: str = Field(default="posted", pattern=r"^(draft|posted)$")
    lines: list[JournalLineBase] = Field(min_length=2)

    @model_validator(mode="after")
    def balanced(self):
        total_d = sum(l.debit for l in self.lines)
        total_c = sum(l.credit for l in self.lines)
        if abs(total_d - total_c) > 0.01:
            raise ValueError(f"Entry not balanced: debit={total_d} credit={total_c}")
        return self


class JournalEntryRead(BaseModel):
    id: int
    tenant_id: int
    entry_number: str
    entry_date: date
    reference: str | None = None
    description: str | None = None
    total_debit: float
    total_credit: float
    status: str
    created_at: datetime | None = None
    lines: list[JournalLineRead] = []
    model_config = ConfigDict(from_attributes=True)


# ---- Fixed Assets ----
class FixedAssetBase(BaseModel):
    asset_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    category: str | None = None
    purchase_date: date
    purchase_cost: float = Field(gt=0)
    salvage_value: float = Field(default=0, ge=0)
    useful_life_years: int = Field(default=5, gt=0)
    depreciation_method: str = Field(default="straight_line", pattern=r"^(straight_line)$")
    notes: str | None = None


class FixedAssetCreate(FixedAssetBase): pass


class FixedAssetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    status: str | None = Field(default=None, pattern=r"^(active|disposed)$")
    notes: str | None = None


class FixedAssetRead(FixedAssetBase):
    id: int
    tenant_id: int
    accumulated_depreciation: float
    status: str
    created_at: datetime | None = None
    # Computed
    net_book_value: float = 0
    annual_depreciation: float = 0
    model_config = ConfigDict(from_attributes=True)


# ---- Bank ----
class BankAccountBase(BaseModel):
    bank_name: str = Field(min_length=1, max_length=150)
    account_number: str = Field(min_length=1, max_length=50)
    account_name: str = Field(min_length=1, max_length=150)
    ifsc_code: str | None = None
    opening_balance: float = Field(default=0)
    gl_account_id: int | None = None
    is_active: bool = True


class BankAccountCreate(BankAccountBase): pass


class BankAccountRead(BankAccountBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None
    current_balance: float = 0
    model_config = ConfigDict(from_attributes=True)


class BankTxnBase(BaseModel):
    bank_account_id: int
    txn_date: date
    description: str = Field(min_length=1, max_length=500)
    reference: str | None = None
    deposit: float = Field(default=0, ge=0)
    withdrawal: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def only_one_side(self):
        if self.deposit > 0 and self.withdrawal > 0:
            raise ValueError("Transaction is either deposit or withdrawal, not both")
        if self.deposit == 0 and self.withdrawal == 0:
            raise ValueError("Must have deposit or withdrawal > 0")
        return self


class BankTxnCreate(BankTxnBase): pass


class BankTxnRead(BankTxnBase):
    id: int
    tenant_id: int
    reconciled: bool
    reconciled_at: datetime | None = None
    journal_entry_id: int | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# ---- Reports ----
class TrialBalanceRow(BaseModel):
    account_id: int
    code: str
    name: str
    account_type: str
    debit: float
    credit: float


class TrialBalance(BaseModel):
    as_of: date
    rows: list[TrialBalanceRow]
    total_debit: float
    total_credit: float


class PnLRow(BaseModel):
    account_type: str
    code: str
    name: str
    amount: float


class ProfitAndLoss(BaseModel):
    period_start: date
    period_end: date
    income: list[PnLRow]
    expenses: list[PnLRow]
    total_income: float
    total_expenses: float
    net_profit: float


class BalanceSheetRow(BaseModel):
    code: str
    name: str
    amount: float


class BalanceSheet(BaseModel):
    as_of: date
    assets: list[BalanceSheetRow]
    liabilities: list[BalanceSheetRow]
    equity: list[BalanceSheetRow]
    total_assets: float
    total_liabilities: float
    total_equity: float
    retained_earnings: float
