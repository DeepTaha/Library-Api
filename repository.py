from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import models

class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, book_data: dict) -> models.Book:
        book = models.Book(**book_data)
        self.db.add(book)
        return book

    # async def get_by_id(self, book_id: int) -> models.Book | None:
    #     result = await self.db.execute(select(models.Book).where(models.Book.id == book_id))
    #     return result.scalar_one_or_none()

    async def list_all(self, available, author, skip, limit):
        query = select(models.Book)

        if available is True:
            query = query.where(models.Book.available_copies > 0)
        elif available is False:
            query = query.where(models.Book.available_copies == 0)

        if author is not None:
            query = query.where(models.Book.author.ilike(f"%{author}%"))

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()
    
    
    async def get_by_id_locked(self, book_id: int) -> models.Book | None:
        result = await self.db.execute(
        select(models.Book).where(models.Book.id == book_id).with_for_update()
    )
        return result.scalar_one_or_none()


class BorrowingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, book_id: int, user_name: str) -> models.Borrowing:
        borrowing = models.Borrowing(book_id=book_id, user_name=user_name)
        self.db.add(borrowing)
        return borrowing

    async def get_by_id(self, borrowing_id: int) -> models.Borrowing | None:
        result = await self.db.execute(select(models.Borrowing).where(models.Borrowing.id == borrowing_id))
        return result.scalar_one_or_none()
    
    async def count_active_by_user(self, user_name: str) -> int:
        result = await self.db.execute(
        select(func.count(models.Borrowing.id))
        .where(models.Borrowing.user_name == user_name)
        .where(models.Borrowing.returned_at.is_(None))
    )
        return result.scalar_one()

    async def find_active_by_user_and_book(self, user_name: str, book_id: int) -> models.Borrowing | None:
        result = await self.db.execute(
        select(models.Borrowing)
        .where(models.Borrowing.user_name == user_name)
        .where(models.Borrowing.book_id == book_id)
        .where(models.Borrowing.returned_at.is_(None))
    )
        return result.scalar_one_or_none()
