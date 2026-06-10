from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app import models
from datetime import datetime, timedelta, timezone


class BorrowingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, book_id: int, user_id: int) -> models.Borrowing:
        now = datetime.now(timezone.utc)
        borrowing = models.Borrowing(
            book_id=book_id,
            user_id=user_id,
            borrowed_at=now,
            due_date=now + timedelta(days=14),
        )
        self.db.add(borrowing)
        return borrowing

    async def get_by_id(self, borrowing_id: int) -> models.Borrowing | None:
        result = await self.db.execute(
            select(models.Borrowing).where(models.Borrowing.id == borrowing_id)
        )
        return result.scalar_one_or_none()

    async def count_active_by_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(models.Borrowing.id))
            .where(models.Borrowing.user_id == user_id)
            .where(models.Borrowing.returned_at.is_(None))
        )
        return result.scalar_one()

    async def find_active_by_user_and_book(self, user_id: int, book_id: int) -> models.Borrowing | None:
        result = await self.db.execute(
            select(models.Borrowing)
            .where(models.Borrowing.user_id == user_id)
            .where(models.Borrowing.book_id == book_id)
            .where(models.Borrowing.returned_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def find_overdue(self):
        now = datetime.utcnow()
        result = await self.db.execute(
            select(models.Borrowing)
            .options(selectinload(models.Borrowing.book))
            .where(models.Borrowing.due_date < now)
            .where(models.Borrowing.returned_at.is_(None))
        )
        return result.scalars().all()
