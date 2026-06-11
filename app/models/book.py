from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    total_copies = Column(Integer, nullable=False, default=0)
    available_copies = Column(Integer, nullable=False, default=0)
    genre = Column(String(100), nullable=True)
    is_age_restricted = Column(Boolean, nullable=False, default=False)

    borrowings = relationship("Borrowing", back_populates="book")
