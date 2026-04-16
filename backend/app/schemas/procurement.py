from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.schemas.inventory import ItemMini, WarehouseMini


# ---- Vendor ----
class VendorBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = None
    gstin: str | None = None
    address: str | None = None
    is_active: bool = True


class VendorCreate(VendorBase): pass


class VendorUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    gstin: str | None = None
    address: str | None = None
    is_active: bool | None = None


class VendorRead(VendorBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class VendorMini(BaseModel):
    id: int
    code: str
    name: str
    model_config = ConfigDict(from_attributes=True)


# ---- Purchase Requisition ----
class PRItemBase(BaseModel):
    item_id: int | None = None
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(gt=0)
    estimated_price: float = Field(default=0, ge=0)


class PRItemRead(PRItemBase):
    id: int
    pr_id: int
    model_config = ConfigDict(from_attributes=True)


class PRCreate(BaseModel):
    pr_number: str = Field(min_length=1, max_length=50)
    pr_date: date
    department: str | None = None
    reason: str | None = None
    items: list[PRItemBase] = Field(min_length=1)


class PRUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(pending|approved|rejected|converted)$")
    approver_comment: str | None = None


class PRRead(BaseModel):
    id: int
    tenant_id: int
    pr_number: str
    pr_date: date
    department: str | None = None
    reason: str | None = None
    status: str
    approver_comment: str | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    items: list[PRItemRead] = []
    model_config = ConfigDict(from_attributes=True)


# ---- Purchase Order ----
class POItemBase(BaseModel):
    item_id: int | None = None
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)


class POItemRead(POItemBase):
    id: int
    po_id: int
    received_quantity: int
    amount: float
    model_config = ConfigDict(from_attributes=True)


class POCreate(BaseModel):
    vendor_id: int
    pr_id: int | None = None
    po_number: str = Field(min_length=1, max_length=50)
    po_date: date
    expected_delivery: date | None = None
    notes: str | None = None
    status: str = Field(default="draft",
                        pattern=r"^(draft|pending_approval|approved|rejected|received|cancelled)$")
    items: list[POItemBase] = Field(min_length=1)


class POUpdate(BaseModel):
    expected_delivery: date | None = None
    notes: str | None = None
    status: str | None = Field(default=None,
                               pattern=r"^(draft|pending_approval|approved|rejected|received|cancelled)$")
    approver_comment: str | None = None


class PORead(BaseModel):
    id: int
    tenant_id: int
    vendor_id: int
    pr_id: int | None = None
    po_number: str
    po_date: date
    expected_delivery: date | None = None
    subtotal: float
    tax_amount: float
    total: float
    status: str
    approver_comment: str | None = None
    approved_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    vendor: VendorMini | None = None
    items: list[POItemRead] = []
    model_config = ConfigDict(from_attributes=True)


# ---- GRN ----
class GRNItemBase(BaseModel):
    po_item_id: int | None = None
    item_id: int | None = None
    description: str = Field(min_length=1, max_length=500)
    received_quantity: int = Field(default=0, ge=0)
    rejected_quantity: int = Field(default=0, ge=0)
    remarks: str | None = None


class GRNItemRead(GRNItemBase):
    id: int
    grn_id: int
    model_config = ConfigDict(from_attributes=True)


class GRNCreate(BaseModel):
    po_id: int
    warehouse_id: int | None = None
    grn_number: str = Field(min_length=1, max_length=50)
    grn_date: date
    notes: str | None = None
    status: str = Field(default="received", pattern=r"^(received|partial|rejected)$")
    items: list[GRNItemBase] = Field(min_length=1)


class GRNRead(BaseModel):
    id: int
    tenant_id: int
    po_id: int
    warehouse_id: int | None = None
    grn_number: str
    grn_date: date
    notes: str | None = None
    status: str
    created_at: datetime | None = None
    warehouse: WarehouseMini | None = None
    items: list[GRNItemRead] = []
    model_config = ConfigDict(from_attributes=True)
