import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id               = Column(Integer, primary_key=True, index=True)
    fine_id          = Column(Integer, ForeignKey("fines.id"), nullable=False)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount           = Column(Integer, nullable=False)         # PKR amount copied from fine at initiation
    order_id         = Column(String(64), nullable=False)      # our internal ref e.g. "LIB-FINE-7-1718900000"
    safepay_tracker  = Column(String(128), nullable=True)      # tracker token returned by Safepay after webhook
    status           = Column(Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=PaymentStatus.PENDING)
    created_at       = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at     = Column(DateTime(timezone=True), nullable=True)
    failure_reason   = Column(String(255), nullable=True)

    fine = relationship("Fine", back_populates="payment")
    user = relationship("User", back_populates="payments")

    # One payment record per fine, and order_id must be globally unique
    # one to one relationship
    __table_args__ = (
        UniqueConstraint("fine_id",  name="uq_payment_fine"),
        UniqueConstraint("order_id", name="uq_payment_order_id"),
        Index("ix_payments_user_id", "user_id"),
    )
