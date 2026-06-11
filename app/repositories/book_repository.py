from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models


class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, book_data: dict) -> models.Book:
        book = models.Book(**book_data)
        self.db.add(book)
        return book

    async def list_all(self, available, author, skip, limit, hide_restricted: bool = False):
        query = select(models.Book)

        if available is True:
            query = query.where(models.Book.available_copies > 0)
        elif available is False:
            query = query.where(models.Book.available_copies == 0)

        if author is not None:
            query = query.where(models.Book.author.ilike(f"%{author}%"))

        if hide_restricted:
            query = query.where(models.Book.is_age_restricted == False)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, book_id: int) -> models.Book | None:
        result = await self.db.execute(
            select(models.Book).where(models.Book.id == book_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_locked(self, book_id: int) -> models.Book | None:
        result = await self.db.execute(
            select(models.Book).where(models.Book.id == book_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def delete(self, book: models.Book) -> None:
        await self.db.delete(book)
