from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "invoice_number", name="uq_tenant_invoice_number"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(14, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(14, 2), nullable=False, default=0)
    discount = Column(Numeric(14, 2), nullable=False, default=0)
    total = Column(Numeric(14, 2), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="draft")  # draft, sent, paid, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)  # GST percentage
    amount = Column(Numeric(14, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
