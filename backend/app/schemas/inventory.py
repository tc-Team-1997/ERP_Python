from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---- Warehouse ----
class WarehouseBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    address: str | None = None
    is_active: bool = True


class WarehouseCreate(WarehouseBase): pass


class WarehouseUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None


class WarehouseRead(WarehouseBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class WarehouseMini(BaseModel):
    id: int
    code: str
    name: str
    model_config = ConfigDict(from_attributes=True)


# ---- Item ----
class ItemBase(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    unit: str = Field(default="unit", max_length=20)
    purchase_price: float = Field(default=0, ge=0)
    sale_price: float = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    is_active: bool = True


class ItemCreate(ItemBase): pass


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    unit: str | None = None
    purchase_price: float | None = Field(default=None, ge=0)
    sale_price: float | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ItemRead(ItemBase):
    id: int
    tenant_id: int
    current_stock: int
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ItemMini(BaseModel):
    id: int
    sku: str
    name: str
    model_config = ConfigDict(from_attributes=True)


# ---- Stock Movement ----
class StockMovementBase(BaseModel):
    item_id: int
    warehouse_id: int
    movement_type: str = Field(pattern=r"^(in|out|transfer|adjustment)$")
    quantity: int = Field(gt=0)
    reference: str | None = None
    notes: str | None = None
    movement_date: date


class StockMovementCreate(StockMovementBase): pass


class StockMovementRead(StockMovementBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None
    item: ItemMini | None = None
    warehouse: WarehouseMini | None = None
    model_config = ConfigDict(from_attributes=True)


class StockSummary(BaseModel):
    item_id: int
    sku: str
    name: str
    current_stock: int
    reorder_level: int
    needs_reorder: bool
