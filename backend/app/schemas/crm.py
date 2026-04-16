from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.schemas.customer import CustomerMini


# ---- Lead ----
class LeadBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    company: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    source: str | None = None
    status: str = Field(default="new", pattern=r"^(new|contacted|qualified|lost)$")
    notes: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    source: str | None = None
    status: str | None = Field(default=None, pattern=r"^(new|contacted|qualified|lost)$")
    notes: str | None = None


class LeadRead(LeadBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ---- Opportunity ----
class OpportunityBase(BaseModel):
    lead_id: int | None = None
    customer_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    expected_amount: float = Field(default=0, ge=0)
    probability: int = Field(default=50, ge=0, le=100)
    stage: str = Field(default="prospecting",
                       pattern=r"^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$")
    expected_close_date: date | None = None
    notes: str | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: str | None = None
    expected_amount: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    stage: str | None = Field(default=None,
                              pattern=r"^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$")
    expected_close_date: date | None = None
    notes: str | None = None


class OpportunityRead(OpportunityBase):
    id: int
    tenant_id: int
    created_at: datetime | None = None
    customer: CustomerMini | None = None

    model_config = ConfigDict(from_attributes=True)


# ---- Quotation ----
class QuotationItemBase(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationItemRead(QuotationItemBase):
    id: int
    quotation_id: int
    amount: float

    model_config = ConfigDict(from_attributes=True)


class QuotationCreate(BaseModel):
    customer_id: int
    quote_number: str = Field(min_length=1, max_length=50)
    quote_date: date
    valid_until: date | None = None
    notes: str | None = None
    status: str = Field(default="draft", pattern=r"^(draft|sent|accepted|rejected|expired)$")
    items: list[QuotationItemCreate] = Field(min_length=1)


class QuotationUpdate(BaseModel):
    valid_until: date | None = None
    status: str | None = Field(default=None, pattern=r"^(draft|sent|accepted|rejected|expired)$")
    notes: str | None = None


class QuotationRead(BaseModel):
    id: int
    tenant_id: int
    customer_id: int
    quote_number: str
    quote_date: date
    valid_until: date | None = None
    subtotal: float
    tax_amount: float
    total: float
    status: str
    notes: str | None = None
    created_at: datetime | None = None
    customer: CustomerMini | None = None
    items: list[QuotationItemRead] = []

    model_config = ConfigDict(from_attributes=True)


# ---- Sales Order ----
class SalesOrderItemBase(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)


class SalesOrderItemCreate(SalesOrderItemBase):
    pass


class SalesOrderItemRead(SalesOrderItemBase):
    id: int
    sales_order_id: int
    amount: float

    model_config = ConfigDict(from_attributes=True)


class SalesOrderCreate(BaseModel):
    customer_id: int
    quotation_id: int | None = None
    order_number: str = Field(min_length=1, max_length=50)
    order_date: date
    delivery_date: date | None = None
    notes: str | None = None
    status: str = Field(default="confirmed",
                        pattern=r"^(draft|confirmed|in_production|delivered|invoiced|cancelled)$")
    items: list[SalesOrderItemCreate] = Field(min_length=1)


class SalesOrderUpdate(BaseModel):
    delivery_date: date | None = None
    status: str | None = Field(default=None,
                               pattern=r"^(draft|confirmed|in_production|delivered|invoiced|cancelled)$")
    notes: str | None = None


class SalesOrderRead(BaseModel):
    id: int
    tenant_id: int
    customer_id: int
    quotation_id: int | None = None
    order_number: str
    order_date: date
    delivery_date: date | None = None
    subtotal: float
    tax_amount: float
    total: float
    status: str
    notes: str | None = None
    created_at: datetime | None = None
    customer: CustomerMini | None = None
    items: list[SalesOrderItemRead] = []

    model_config = ConfigDict(from_attributes=True)
