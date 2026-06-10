"""User model — stores authentication and authorization data."""
import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class UserRole(str, enum.Enum):
    """The three roles a user can have."""
    ADMIN = "admin"
    LIBRARIAN = "librarian"
    READER = "reader"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.READER)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # A user can have many borrowings
    borrowings = relationship("Borrowing", back_populates="user")