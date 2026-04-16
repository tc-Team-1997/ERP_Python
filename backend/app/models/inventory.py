from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_tenant_warehouse_code"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="warehouses")
    stock_movements = relationship("StockMovement", back_populates="warehouse", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_tenant_item_sku"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(20), nullable=False, default="unit")  # unit, kg, ltr, box...
    purchase_price = Column(Numeric(14, 2), nullable=False, default=0)
    sale_price = Column(Numeric(14, 2), nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=0)
    current_stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="items")
    stock_movements = relationship("StockMovement", back_populates="item", cascade="all, delete-orphan")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_type = Column(String(20), nullable=False)  # in, out, transfer, adjustment
    quantity = Column(Integer, nullable=False)
    reference = Column(String(100), nullable=True)  # PO#, GRN#, manual reference
    notes = Column(Text, nullable=True)
    movement_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="stock_movements")
    item = relationship("Item", back_populates="stock_movements")
    warehouse = relationship("Warehouse", back_populates="stock_movements")
