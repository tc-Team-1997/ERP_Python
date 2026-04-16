from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Vendor(Base):
    __tablename__ = "vendors"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_tenant_vendor_code"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    gstin = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="vendors")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor", cascade="all, delete-orphan")


class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"
    __table_args__ = (UniqueConstraint("tenant_id", "pr_number", name="uq_tenant_pr_number"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    pr_number = Column(String(50), nullable=False)
    pr_date = Column(Date, nullable=False)
    department = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, converted
    approver_comment = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="purchase_requisitions")
    items = relationship("PurchaseRequisitionItem", back_populates="pr", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="pr")


class PurchaseRequisitionItem(Base):
    __tablename__ = "pr_items"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, ForeignKey("purchase_requisitions.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    estimated_price = Column(Numeric(14, 2), nullable=False, default=0)

    pr = relationship("PurchaseRequisition", back_populates="items")
    item = relationship("Item")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (UniqueConstraint("tenant_id", "po_number", name="uq_tenant_po_number"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    pr_id = Column(Integer, ForeignKey("purchase_requisitions.id", ondelete="SET NULL"), nullable=True, index=True)
    po_number = Column(String(50), nullable=False)
    po_date = Column(Date, nullable=False)
    expected_delivery = Column(Date, nullable=True)
    subtotal = Column(Numeric(14, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(14, 2), nullable=False, default=0)
    total = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="draft")
    # draft, pending_approval, approved, rejected, received, cancelled
    approver_comment = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="purchase_orders")
    vendor = relationship("Vendor", back_populates="purchase_orders")
    pr = relationship("PurchaseRequisition", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="po", cascade="all, delete-orphan")
    grns = relationship("GoodsReceiptNote", back_populates="po", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "po_items"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    received_quantity = Column(Integer, nullable=False, default=0)
    unit_price = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    amount = Column(Numeric(14, 2), nullable=False)

    po = relationship("PurchaseOrder", back_populates="items")
    item = relationship("Item")


class GoodsReceiptNote(Base):
    __tablename__ = "goods_receipt_notes"
    __table_args__ = (UniqueConstraint("tenant_id", "grn_number", name="uq_tenant_grn_number"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True)
    grn_number = Column(String(50), nullable=False)
    grn_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="received")  # received, partial, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="grns")
    po = relationship("PurchaseOrder", back_populates="grns")
    warehouse = relationship("Warehouse")
    items = relationship("GRNItem", back_populates="grn", cascade="all, delete-orphan")


class GRNItem(Base):
    __tablename__ = "grn_items"

    id = Column(Integer, primary_key=True, index=True)
    grn_id = Column(Integer, ForeignKey("goods_receipt_notes.id", ondelete="CASCADE"), nullable=False, index=True)
    po_item_id = Column(Integer, ForeignKey("po_items.id", ondelete="SET NULL"), nullable=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    received_quantity = Column(Integer, nullable=False, default=0)
    rejected_quantity = Column(Integer, nullable=False, default=0)
    remarks = Column(Text, nullable=True)

    grn = relationship("GoodsReceiptNote", back_populates="items")
    po_item = relationship("PurchaseOrderItem")
    item = relationship("Item")
