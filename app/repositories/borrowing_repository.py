from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import case, func
from sqlalchemy.orm import selectinload, joinedload
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
            .with_for_update()
        )
        return result.scalar_one()

    async def find_active_by_user_and_book(self, user_id: int, book_id: int) -> models.Borrowing | None:
        result = await self.db.execute(
            select(models.Borrowing)
            .where(models.Borrowing.user_id == user_id)
            .where(models.Borrowing.book_id == book_id)
            .where(models.Borrowing.returned_at.is_(None))
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int, returned: bool | None = None) -> list[models.Borrowing]:
        query = select(models.Borrowing).where(models.Borrowing.user_id == user_id)
        if returned is False:
            query = query.where(models.Borrowing.returned_at.is_(None))
        elif returned is True:
            query = query.where(models.Borrowing.returned_at.isnot(None))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_all(
        self,
        user_id: int | None = None,
        book_id: int | None = None,
        active: bool | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[models.Borrowing]:
        query = select(models.Borrowing)
        if user_id is not None:
            query = query.where(models.Borrowing.user_id == user_id)
        if book_id is not None:
            query = query.where(models.Borrowing.book_id == book_id)
        if active is True:
            query = query.where(models.Borrowing.returned_at.is_(None))
        elif active is False:
            query = query.where(models.Borrowing.returned_at.isnot(None))
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_by_book(self, book_id: int) -> list[models.Borrowing]:
        result = await self.db.execute(
            select(models.Borrowing).where(models.Borrowing.book_id == book_id)
        )
        return result.scalars().all()

    async def find_overdue(self):
        """" go into the borrowings table. Find every borrowing where the due date has 
         already passed AND the book hasn't been returned yet. Also bring along the related
         book and user data while you're at it."""
         
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(models.Borrowing)
            .options(
                selectinload(models.Borrowing.book),
                selectinload(models.Borrowing.user),
            )
            .where(models.Borrowing.due_date < now)
            .where(models.Borrowing.returned_at.is_(None))
        )
        return result.scalars().all()

    async def find_newly_overdue(self):
        """Overdue borrowings not yet flagged — used by the background job."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(models.Borrowing)
            .options(
                selectinload(models.Borrowing.book),
                selectinload(models.Borrowing.user),
            )
            .where(models.Borrowing.due_date < now)
            .where(models.Borrowing.returned_at.is_(None))
            .where(models.Borrowing.is_overdue.is_(False))
        )
        return result.scalars().all()

    async def count_active_overdue_by_user(self, user_id: int) -> int:
        """Count unreturned borrowings that are marked overdue for the given user."""
        result = await self.db.execute(
            select(func.count(models.Borrowing.id))
            .where(models.Borrowing.user_id == user_id)
            .where(models.Borrowing.returned_at.is_(None))
            .where(models.Borrowing.is_overdue.is_(True))
        )
        return result.scalar_one()

    async def stream_history_by_user(self, user_id: int):
        """Async generator that yields borrowings one at a time, fetching in batches of 100."""
        query = (
            select(models.Borrowing)
            .options(joinedload(models.Borrowing.book))
            .where(models.Borrowing.user_id == user_id)
            .order_by(models.Borrowing.borrowed_at)
            .execution_options(yield_per=100)
        )
        result = await self.db.stream_scalars(query)
        async for borrowing in result:
            yield borrowing

    async def get_analytics_summary(self) -> dict:
        now = datetime.now(timezone.utc)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Single pass over borrowings for all scalar stats.
        stats_result = await self.db.execute(
            select(
                func.count(
                    case(
                        (models.Borrowing.borrowed_at >= this_month_start, 1),
                        else_=None,
                    )
                ).label("this_month"), # count of books borrowed this month
                func.count(
                    case(
                        (
                            (models.Borrowing.borrowed_at >= last_month_start)
                            & (models.Borrowing.borrowed_at < this_month_start),
                            1,
                        ),
                        else_=None,
                    )
                ).label("last_month"), # books borrowed previous months
                # COUNT(DISTINCT ...) ignores NULLs, so CASE returning NULL for
                # non-overdue rows means we only count distinct overdue user_ids.
                func.count(
                    func.distinct(
                        case(
                            (
                                (models.Borrowing.is_overdue == True)
                                & (models.Borrowing.returned_at.is_(None)),
                                models.Borrowing.user_id,
                            ),
                            else_=None,
                        )
                    )
                ).label("overdue_readers"),
            )
        )
        stats = stats_result.one()

        # Average days kept — computed in Python to avoid DB-specific interval arithmetic.
        durations_result = await self.db.execute(
            select(models.Borrowing.borrowed_at, models.Borrowing.returned_at)
            .where(models.Borrowing.returned_at.isnot(None))
        )
        durations = durations_result.all()
        if durations:
            total_seconds = sum(
                (row.returned_at - row.borrowed_at).total_seconds()
                for row in durations
            )
            avg_days_kept = round(total_seconds / len(durations) / 86400.0, 2)
        else:
            avg_days_kept = None

        # Top 5 most borrowed books of all time.
        top_books_result = await self.db.execute(
            select(
                models.Book.id,
                models.Book.title,
                models.Book.author,
                func.count(models.Borrowing.id).label("borrow_count"),
            )
            .join(models.Borrowing, models.Book.id == models.Borrowing.book_id)
            .group_by(models.Book.id, models.Book.title, models.Book.author)
            .order_by(func.count(models.Borrowing.id).desc())
            .limit(5)
        )
        top_books = top_books_result.all()

        return {
            "borrowed_this_month": stats.this_month,
            "borrowed_last_month": stats.last_month,
            "readers_with_overdue": stats.overdue_readers,
            "avg_days_kept": avg_days_kept,
            "top_5_books": [
                {
                    "book_id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "borrow_count": row.borrow_count,
                }
                for row in top_books
            ],
        }
