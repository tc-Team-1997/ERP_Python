from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_code", name="uq_tenant_employee_code"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_code = Column(String(50), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    joining_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="employees")
    salary_structure = relationship("SalaryStructure", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    payroll_records = relationship("PayrollRecord", back_populates="employee", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")
