from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_id", "date", name="uq_tenant_emp_att_date"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)
    status = Column(String(20), nullable=False, default="present")  # present, absent, half_day, leave
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="attendances")
    employee = relationship("Employee", back_populates="attendances")
