import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from app.exceptions import (
    FineNotFound,
    FineAlreadyPaid,
    FineNotBelongToUser,
    PaymentNotFound,
    InvalidPaymentCallback,
    SafepayAPIError,
)
from app.models import User
from app.models.fine import FineStatus
from app.repositories.fine_repository import FineRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentInitiateResponse


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fine_repo = FineRepository(db)        # helpers know how to read/write fines.
        self.payment_repo = PaymentRepository(db)  # helpers know how to read/write payments.

    # ------------------------------------------------------------------ #
    #  Safepay API call — creates a tracker and returns its token          #
    # ------------------------------------------------------------------ #

    @property
    def _safepay_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {config.SAFEPAY_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    async def _create_safepay_tracker(self, amount_pkr: int, order_id: str) -> str:
        """
        Calls POST /order/v1/init on Safepay.
        Returns the tracker token string (e.g. "track_ac6afa9c-...").
        Raises SafepayAPIError if Safepay returns a non-ok response.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{config.SAFEPAY_BASE_URL}/order/v1/init",
                json={
                    "merchant_api_key": config.SAFEPAY_API_KEY,
                    "intent": "CYBERSOURCE",
                    "mode": "payment",
                    "currency": "PKR",
                    "amount": amount_pkr,
                    "environment": "sandbox" if config.SAFEPAY_SANDBOX else "production",
                    "client": config.SAFEPAY_API_KEY,
                    "metadata": {"order_id": order_id, "source": "custom"},
                },
                headers=self._safepay_headers,
            )

        data = response.json()
        if data.get("status", {}).get("message") != "success":
            import logging
            logging.getLogger("payment").error(
                "Safepay API error | status=%s | body=%s", response.status_code, data
            )
            raise SafepayAPIError(data)

        return data["data"]["token"]

    async def _create_safepay_passport(self) -> str:
        """Calls POST /client/passport/v1/token. Returns the short-lived JWT (tbt)."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{config.SAFEPAY_BASE_URL}/client/passport/v1/token",
                json={"merchant_api_key": config.SAFEPAY_API_KEY},
                headers={
                    "Content-Type": "application/json",
                    "x-sfpy-merchant-secret": config.SAFEPAY_SECRET_KEY,
                },
            )
        data = response.json()
        if response.is_error:
            import logging
            logging.getLogger("payment").error(
                "Safepay passport error | status=%s | body=%s", response.status_code, data
            )
            raise SafepayAPIError(data)
        return data["data"]

    # ------------------------------------------------------------------ #
    #  Build the checkout URL Ahmed opens in his browser                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_checkout_url(tracker_token: str, tbt: str, order_id: str) -> str:
        env = "sandbox" if config.SAFEPAY_SANDBOX else "production"
        params = urlencode({
            "environment": env,
            "tbt": tbt,
            "tracker": tracker_token,
            "source": "custom",
            "order_id": order_id,
            "redirect_url": config.SAFEPAY_SUCCESS_URL,
            "cancel_url": config.SAFEPAY_CANCEL_URL,
        })
        return f"{config.SAFEPAY_CHECKOUT_URL}?{params}"

    # ------------------------------------------------------------------ #
    #  Webhook signature verification                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def verify_webhook_signature(tracker_token: str, received_signature: str) -> bool:
        """
        Safepay signs webhooks with:
            HMAC-SHA256(key=WEBHOOK_SECRET, message=tracker_token)
        We compute the same hash and compare — if they match, the webhook
        is genuinely from Safepay and has not been tampered with.
        """
        expected = hmac.new(
            config.SAFEPAY_WEBHOOK_SECRET.encode(),
            tracker_token.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, received_signature)

    # ------------------------------------------------------------------ #
    #  Initiate payment — called by POST /payments/initiate                #
    # ------------------------------------------------------------------ #

    async def initiate_payment(
        self,
        fine_id: int,
        current_user: User,
    ) -> PaymentInitiateResponse:
        # 1. Fine must exist
        fine = await self.fine_repo.get_by_id(fine_id)
        if not fine:
            raise FineNotFound()

        # 2. Fine must belong to the requesting user
        if fine.user_id != current_user.id:
            raise FineNotBelongToUser()

        # 3. Fine must still be pending (not already paid or waived)
        if fine.status != FineStatus.PENDING:
            raise FineAlreadyPaid()

        # 4. If a pending payment already exists for this fine, reuse the record
        #    but mint a FRESH tracker + tbt. Safepay trackers go stale (they expire
        #    and are invalidated when the merchant secret is rotated), so reusing the
        #    stored tracker yields "cannot find tracker with token ... using keys" on
        #    the checkout page. A new tracker is cheap; the order_id is regenerated too.
        existing_payment = await self.payment_repo.get_by_fine_id(fine_id)
        if existing_payment:
            # Capture the id before commit — committing expires the ORM object,
            # so reading existing_payment.id afterwards would trigger a lazy DB
            # load in a sync context (MissingGreenlet).
            existing_payment_id = existing_payment.id
            order_id = f"LIB-FINE-{fine_id}-{int(time.time())}"
            tracker_token = await self._create_safepay_tracker(fine.amount, order_id)
            tbt = await self._create_safepay_passport()
            await self.payment_repo.update_tracker(
                existing_payment_id, order_id, tracker_token
            )
            await self.db.commit()
            checkout_url = self._build_checkout_url(tracker_token, tbt, order_id)
            return PaymentInitiateResponse(
                payment_id=existing_payment_id,
                order_id=order_id,
                checkout_url=checkout_url,
            )

        # 5. Generate a unique order ID: LIB-FINE-{fine_id}-{unix_timestamp}
        order_id = f"LIB-FINE-{fine_id}-{int(time.time())}"

        # 6. Call Safepay API to create a tracker and passport concurrently
        tracker_token = await self._create_safepay_tracker(fine.amount, order_id)
        tbt = await self._create_safepay_passport()

        # 7. Save a pending payment record to DB
        payment = await self.payment_repo.create(
            fine_id=fine_id,
            user_id=current_user.id,
            amount=fine.amount,
            order_id=order_id,
            safepay_tracker=tracker_token,
        )
        await self.db.commit()
        await self.db.refresh(payment)

        # 8. Build the Safepay checkout URL and return it
        checkout_url = self._build_checkout_url(tracker_token, tbt, order_id)
        return PaymentInitiateResponse(
            payment_id=payment.id,
            order_id=order_id,
            checkout_url=checkout_url,
        )

    # ------------------------------------------------------------------ #
    #  Process webhook — called by POST /payments/webhook                  #
    # ------------------------------------------------------------------ #

    async def process_webhook(self, payload: dict, signature: str) -> None:
        """
        Safepay POSTs here after Ahmed completes (or fails) payment.
        Payload contains: tracker, order_id, status ("SUCCESS" or "FAILED").
        The X-SFPY-SIGNATURE header is the HMAC of the tracker token.
        """
        tracker_token = payload.get("tracker", "")

        # 1. Verify the signature — reject anything that doesn't match
        if not self.verify_webhook_signature(tracker_token, signature):
            raise InvalidPaymentCallback()

        order_id = payload.get("order_id", "")
        status   = payload.get("status", "")

        # 2. Find our payment record by order_id
        payment = await self.payment_repo.get_by_order_id(order_id)
        if not payment:
            raise PaymentNotFound()

        if status == "SUCCESS":
            # 3a. Mark the payment as completed
            await self.payment_repo.mark_completed(payment.id, tracker_token)

            # 3b. Mark the fine as paid
            await self.fine_repo.mark_paid(payment.fine_id)

            await self.db.commit()

            # 3c. Send receipt email (best-effort — failure must not fail the webhook)
            try:
                from app.email_sender import send_payment_receipt
                from app.repositories.user_repository import UserRepository
                user = await UserRepository(self.db).get_by_id(payment.user_id)
                fine = await self.fine_repo.get_by_id(payment.fine_id)
                if user and user.email and fine:
                    await send_payment_receipt(
                        user_email=user.email,
                        username=user.username,
                        amount=payment.amount,
                        order_id=order_id,
                        fine_reason=f"{fine.days_overdue} day(s) overdue",
                    )
            except Exception:
                import logging
                logging.getLogger("payment").exception(
                    "Failed to send payment receipt for order %s", order_id
                )
        else:
            # 3d. Payment failed — record reason, fine stays pending
            reason = payload.get("reference_code", "Payment failed")
            await self.payment_repo.mark_failed(payment.id, tracker_token, reason)
            await self.db.commit()
