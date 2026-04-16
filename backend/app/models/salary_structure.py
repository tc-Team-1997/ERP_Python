from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_id", name="uq_tenant_employee_salary"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    basic = Column(Numeric(12, 2), nullable=False)
    hra = Column(Numeric(12, 2), nullable=False, default=0)
    allowances = Column(Numeric(12, 2), nullable=False, default=0)
    deductions = Column(Numeric(12, 2), nullable=False, default=0)
    tax_percent = Column(Numeric(5, 2), nullable=False, default=0)
    effective_from = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="salary_structures")
    employee = relationship("Employee", back_populates="salary_structure")
