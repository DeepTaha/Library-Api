from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from app.database import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
