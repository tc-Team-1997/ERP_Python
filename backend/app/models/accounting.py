from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_tenant_account_code"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(150), nullable=False)
    # account_type: asset, liability, equity, income, expense
    account_type = Column(String(20), nullable=False)
    parent_id = Column(Integer, ForeignKey("chart_of_accounts.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="accounts")
    journal_lines = relationship("JournalLine", back_populates="account", cascade="all, delete-orphan")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (UniqueConstraint("tenant_id", "entry_number", name="uq_tenant_je_number"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_number = Column(String(50), nullable=False)
    entry_date = Column(Date, nullable=False)
    reference = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    total_debit = Column(Numeric(14, 2), nullable=False, default=0)
    total_credit = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="posted")  # draft, posted, reversed
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="journal_entries")
    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    debit = Column(Numeric(14, 2), nullable=False, default=0)
    credit = Column(Numeric(14, 2), nullable=False, default=0)
    narration = Column(String(500), nullable=True)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartOfAccounts", back_populates="journal_lines")


class FixedAsset(Base):
    __tablename__ = "fixed_assets"
    __table_args__ = (UniqueConstraint("tenant_id", "asset_code", name="uq_tenant_asset_code"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # building, vehicle, equipment, furniture
    purchase_date = Column(Date, nullable=False)
    purchase_cost = Column(Numeric(14, 2), nullable=False)
    salvage_value = Column(Numeric(14, 2), nullable=False, default=0)
    useful_life_years = Column(Integer, nullable=False, default=5)
    depreciation_method = Column(String(20), nullable=False, default="straight_line")
    accumulated_depreciation = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active")  # active, disposed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="fixed_assets")


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    __table_args__ = (UniqueConstraint("tenant_id", "account_number", name="uq_tenant_bank_account"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_name = Column(String(150), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_name = Column(String(150), nullable=False)
    ifsc_code = Column(String(20), nullable=True)
    opening_balance = Column(Numeric(14, 2), nullable=False, default=0)
    gl_account_id = Column(Integer, ForeignKey("chart_of_accounts.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="bank_accounts")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    txn_date = Column(Date, nullable=False)
    description = Column(String(500), nullable=False)
    reference = Column(String(100), nullable=True)
    deposit = Column(Numeric(14, 2), nullable=False, default=0)
    withdrawal = Column(Numeric(14, 2), nullable=False, default=0)
    reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bank_account = relationship("BankAccount", back_populates="transactions")
