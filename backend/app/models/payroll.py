from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_id", "month", "year", name="uq_tenant_employee_monthly_payroll"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic = Column(Numeric(12, 2), nullable=False)
    hra = Column(Numeric(12, 2), nullable=False, default=0)
    allowances = Column(Numeric(12, 2), nullable=False, default=0)
    gross_salary = Column(Numeric(12, 2), nullable=False)
    deductions = Column(Numeric(12, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    net_salary = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False, default="processed")
    processed_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="payroll_records")
    employee = relationship("Employee", back_populates="payroll_records")
