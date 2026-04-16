from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    source = Column(String(50), nullable=True)  # website, referral, cold_call, event...
    status = Column(String(20), nullable=False, default="new")  # new, contacted, qualified, lost
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="leads")
    opportunities = relationship("Opportunity", back_populates="lead", cascade="all, delete-orphan")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    expected_amount = Column(Numeric(14, 2), nullable=False, default=0)
    probability = Column(Integer, nullable=False, default=50)  # 0-100
    stage = Column(String(30), nullable=False, default="prospecting")
    # prospecting, qualification, proposal, negotiation, closed_won, closed_lost
    expected_close_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="opportunities")
    lead = relationship("Lead", back_populates="opportunities")
    customer = relationship("Customer")


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    quote_number = Column(String(50), nullable=False)
    quote_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    subtotal = Column(Numeric(14, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(14, 2), nullable=False, default=0)
    total = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="draft")  # draft, sent, accepted, rejected, expired
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="quotations")
    customer = relationship("Customer")
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    amount = Column(Numeric(14, 2), nullable=False)

    quotation = relationship("Quotation", back_populates="items")


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True, index=True)
    order_number = Column(String(50), nullable=False)
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(14, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(14, 2), nullable=False, default=0)
    total = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="confirmed")
    # draft, confirmed, in_production, delivered, invoiced, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="sales_orders")
    customer = relationship("Customer")
    quotation = relationship("Quotation")
    items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan")


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(Integer, primary_key=True, index=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    amount = Column(Numeric(14, 2), nullable=False)

    sales_order = relationship("SalesOrder", back_populates="items")
