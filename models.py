"""SQLAlchemy ORM models: the actual database tables for the library API."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from database import Base


# Represents a book in the catalog and how many copies exist vs. are free.
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    total_copies = Column(Integer, nullable=False, default=0)
    available_copies = Column(Integer, nullable=False, default=0)
    genre=Column(String(100), nullable= True)

    borrowings = relationship("Borrowing", back_populates="book")


# Records a single borrow event; returned_at stays NULL until the book is back.
class Borrowing(Base):
    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_name = Column(String, nullable=False)
    borrowed_at = Column(DateTime(timezone=True), default=func.now()) 
    returned_at = Column(DateTime(timezone=True), nullable=True)

    book = relationship("Book", back_populates="borrowings")
