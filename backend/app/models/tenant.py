from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="tenant", cascade="all, delete-orphan")
    salary_structures = relationship("SalaryStructure", back_populates="tenant", cascade="all, delete-orphan")
    payroll_records = relationship("PayrollRecord", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="tenant", cascade="all, delete-orphan")
    expense_categories = relationship("ExpenseCategory", back_populates="tenant", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="tenant", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="tenant", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="tenant", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="tenant", cascade="all, delete-orphan")
    sales_orders = relationship("SalesOrder", back_populates="tenant", cascade="all, delete-orphan")
    warehouses = relationship("Warehouse", back_populates="tenant", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="tenant", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="tenant", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="tenant", cascade="all, delete-orphan")
    purchase_requisitions = relationship("PurchaseRequisition", back_populates="tenant", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="tenant", cascade="all, delete-orphan")
    grns = relationship("GoodsReceiptNote", back_populates="tenant", cascade="all, delete-orphan")
    accounts = relationship("ChartOfAccounts", back_populates="tenant", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="tenant", cascade="all, delete-orphan")
    fixed_assets = relationship("FixedAsset", back_populates="tenant", cascade="all, delete-orphan")
    bank_accounts = relationship("BankAccount", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")
