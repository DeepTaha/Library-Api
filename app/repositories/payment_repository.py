from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models
from app.models.payment import PaymentStatus


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        fine_id: int,
        user_id: int,
        amount: int,
        order_id: str,
        safepay_tracker: str,
    ) -> models.Payment:
        payment = models.Payment(
            fine_id=fine_id,
            user_id=user_id,
            amount=amount,
            order_id=order_id,
            safepay_tracker=safepay_tracker,
            status=PaymentStatus.PENDING,
        )
        self.db.add(payment)
        return payment

    async def get_by_id(self, payment_id: int) -> models.Payment | None:
        result = await self.db.execute(
            select(models.Payment).where(models.Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_order_id(self, order_id: str) -> models.Payment | None:
        """Used in the Safepay webhook to match the callback to the right payment record."""
        result = await self.db.execute(
            select(models.Payment).where(models.Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_fine_id(self, fine_id: int) -> models.Payment | None:
        """Return an active (non-failed) payment for this fine, so retries aren't blocked."""
        result = await self.db.execute(
            select(models.Payment).where(
                models.Payment.fine_id == fine_id,
                models.Payment.status != PaymentStatus.FAILED,
            )
        )
        return result.scalar_one_or_none()

    async def update_tracker(
        self,
        payment_id: int,
        order_id: str,
        safepay_tracker: str,
    ) -> models.Payment | None:
        """Refresh the Safepay tracker/order on a pending payment that is being retried."""
        payment = await self.get_by_id(payment_id)
        if payment:
            payment.order_id = order_id
            payment.safepay_tracker = safepay_tracker
        return payment

    async def mark_completed(
        self,
        payment_id: int,
        safepay_tracker: str,
    ) -> models.Payment | None:
        payment = await self.get_by_id(payment_id)
        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.safepay_tracker = safepay_tracker
            payment.completed_at = datetime.now(timezone.utc)
        return payment

    async def mark_failed(
        self,
        payment_id: int,
        safepay_tracker: str,
        reason: str,
    ) -> models.Payment | None:
        payment = await self.get_by_id(payment_id)
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.safepay_tracker = safepay_tracker
            payment.failure_reason = reason
        return payment

    async def list_by_user(self, user_id: int) -> list[models.Payment]:
        result = await self.db.execute(
            select(models.Payment)
            .where(models.Payment.user_id == user_id)
            .order_by(models.Payment.created_at.desc())
        )
        return result.scalars().all()

    async def list_all(self, offset: int = 0, limit: int = 20) -> list[models.Payment]:
        result = await self.db.execute(
            select(models.Payment)
            .order_by(models.Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
