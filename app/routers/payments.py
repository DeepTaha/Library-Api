from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import require_any_role, require_librarian
from app.models import User, UserRole
from app.repositories.payment_repository import PaymentRepository
from app.services.payment_service import PaymentService
from app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentStatusResponse,
)
from app.exceptions import InsufficientPermissions, PaymentNotFound

router = APIRouter(prefix="/payments", tags=["payments"])



@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=201)
async def initiate_payment(
    body: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """
    Start a Safepay payment for an outstanding fine.
    Returns a checkout_url — the frontend redirects Ahmed to this URL.
    """
    service = PaymentService(db)
    return await service.initiate_payment(body.fine_id, current_user)


@router.post("/webhook")
async def safepay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Safepay calls this endpoint after Ahmed completes or cancels payment.
    No authentication — Safepay posts here directly.
    Signature in X-SFPY-SIGNATURE header is verified inside the service.
    """
    payload   = await request.json()
    signature = request.headers.get("X-SFPY-SIGNATURE", "")

    service = PaymentService(db)
    await service.process_webhook(payload, signature)

    # Must return 200 — Safepay retries if it gets anything else
    return JSONResponse(status_code=200, content={"status": "ok"})


@router.get("/me", response_model=list[PaymentStatusResponse])
async def get_my_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Get payment history for the logged-in user."""
    payment_repo = PaymentRepository(db)
    return await payment_repo.list_by_user(current_user.id)


@router.get("/", response_model=list[PaymentStatusResponse])
async def list_all_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """List all payments across all users. Librarian/admin only."""
    payment_repo = PaymentRepository(db)
    return await payment_repo.list_all()


@router.get("/success")
async def payment_success(request: Request):
    """
    Safepay redirects Ahmed here after a successful payment.
    The actual fine/payment update happens in the webhook — this is just
    the landing page Ahmed sees in his browser.
    """
    return JSONResponse(
        status_code=200,
        content={"message": "Payment completed. Your fine has been cleared."},
    )


@router.get("/cancel")
async def payment_cancel(request: Request):
    """
    Safepay redirects Ahmed here if he cancels on the checkout page.
    Fine remains pending — he can try again anytime.
    """
    return JSONResponse(
        status_code=200,
        content={"message": "Payment cancelled. Your fine is still outstanding."},
    )


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Get a single payment. Readers can only see their own; librarian/admin can see any."""
    payment_repo = PaymentRepository(db)
    payment = await payment_repo.get_by_id(payment_id)

    if not payment:
        raise PaymentNotFound()

    if (payment.user_id != current_user.id
            and current_user.role not in (UserRole.ADMIN, UserRole.LIBRARIAN)):
        raise InsufficientPermissions()

    return payment
