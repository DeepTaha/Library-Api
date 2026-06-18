from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models
from app.models.fine import FineStatus


class FineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        borrowing_id: int,
        user_id: int,
        days_overdue: int,
        amount: int,
    ) -> models.Fine:
        fine = models.Fine(
            borrowing_id=borrowing_id,
            user_id=user_id,
            days_overdue=days_overdue,
            amount=amount,
            status=FineStatus.PENDING,
        )
        self.db.add(fine)
        return fine

    async def get_by_id(self, fine_id: int) -> models.Fine | None:
        result = await self.db.execute(
            select(models.Fine).where(models.Fine.id == fine_id)
        )
        return result.scalar_one_or_none()

    async def get_by_borrowing_id(self, borrowing_id: int) -> models.Fine | None:
        """Check if a fine already exists for a borrowing — prevents duplicates."""
        result = await self.db.execute(
            select(models.Fine).where(models.Fine.borrowing_id == borrowing_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_by_user(self, user_id: int) -> list[models.Fine]:
        """Used in borrow_book() to block borrowing while unpaid fines exist."""
        result = await self.db.execute(
            select(models.Fine)
            .where(models.Fine.user_id == user_id)
            .where(models.Fine.status == FineStatus.PENDING)
        )
        return result.scalars().all()

    async def list_by_user(
        self,
        user_id: int,
        status: FineStatus | None = None,
    ) -> list[models.Fine]:
        query = select(models.Fine).where(models.Fine.user_id == user_id)
        if status is not None:
            query = query.where(models.Fine.status == status)
        query = query.order_by(models.Fine.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_all(
        self,
        status: FineStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Fine]:
        query = select(models.Fine)
        if status is not None:
            query = query.where(models.Fine.status == status)
        query = query.order_by(models.Fine.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_paid(self, fine_id: int) -> models.Fine | None:
        fine = await self.get_by_id(fine_id)
        if fine:
            fine.status = FineStatus.PAID
            fine.paid_at = datetime.now(timezone.utc)
        return fine

    async def mark_waived(self, fine_id: int) -> models.Fine | None:
        fine = await self.get_by_id(fine_id)
        if fine:
            fine.status = FineStatus.WAIVED
        return fine
