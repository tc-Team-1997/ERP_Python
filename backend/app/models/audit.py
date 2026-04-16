from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)  # snapshot in case user is deleted
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, APPROVE, REJECT, LOGIN, etc.
    resource_type = Column(String(50), nullable=False)  # e.g. invoice, po, employee
    resource_id = Column(Integer, nullable=True)
    description = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    tenant = relationship("Tenant", back_populates="audit_logs")
