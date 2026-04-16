from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_tenant_customer_email"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    gstin = Column(String(20), nullable=True)
    billing_address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
