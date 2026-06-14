from sqlalchemy import Column, String, DateTime
from app.database import Base


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    jti = Column(String(36), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
