from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Borrowing(Base):
    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"),nullable=False)
    borrowed_at = Column(DateTime(timezone=True), default=func.now())
    due_date = Column(DateTime, nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)

    book = relationship("Book", back_populates="borrowings")
    user = relationship("User", back_populates="borrowings")
