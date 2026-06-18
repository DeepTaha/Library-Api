import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Enum, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.database import Base


class FineStatus(str, enum.Enum):
    PENDING = "pending"
    PAID    = "paid"
    WAIVED  = "waived"


class Fine(Base):
    __tablename__ = "fines"

    id           = Column(Integer, primary_key=True, index=True)
    borrowing_id = Column(Integer, ForeignKey("borrowings.id"), nullable=False)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    days_overdue = Column(Integer, nullable=False)
    amount       = Column(Integer, nullable=False)  # PKR, e.g. 50
    status       = Column(Enum(FineStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=FineStatus.PENDING)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    paid_at      = Column(DateTime(timezone=True), nullable=True)

    borrowing = relationship("Borrowing", back_populates="fine")
    user      = relationship("User", back_populates="fines")
    payment   = relationship("Payment", back_populates="fine", uselist=False)

    # One fine per borrowing — returning a book late twice isn't possible
    __table_args__ = (
        UniqueConstraint("borrowing_id", name="uq_fine_borrowing"),
        Index("ix_fines_user_status", "user_id", "status"),
    )
