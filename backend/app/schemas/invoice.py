from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.customer import CustomerMini


class InvoiceItemBase(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemRead(InvoiceItemBase):
    id: int
    invoice_id: int
    amount: float

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    customer_id: int
    invoice_number: str = Field(min_length=1, max_length=50)
    invoice_date: date
    due_date: date | None = None
    discount: float = Field(default=0, ge=0)
    notes: str | None = None
    status: str = Field(default="draft", pattern=r"^(draft|sent|paid|cancelled)$")


class InvoiceCreate(InvoiceBase):
    items: list[InvoiceItemCreate] = Field(min_length=1)


class InvoiceUpdate(BaseModel):
    customer_id: int | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    discount: float | None = Field(default=None, ge=0)
    notes: str | None = None
    status: str | None = Field(default=None, pattern=r"^(draft|sent|paid|cancelled)$")
    items: list[InvoiceItemCreate] | None = None


class InvoiceRead(BaseModel):
    id: int
    tenant_id: int
    customer_id: int
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    subtotal: float
    tax_amount: float
    discount: float
    total: float
    notes: str | None = None
    status: str
    created_at: datetime | None = None
    customer: CustomerMini | None = None
    items: list[InvoiceItemRead] = []

    model_config = ConfigDict(from_attributes=True)
