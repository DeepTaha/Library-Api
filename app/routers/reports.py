from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db, SessionLocal
from app.models import User, Borrowing
from app.repositories.user_repository import UserRepository
from app.security import require_librarian
from app.exceptions import UserNotFound
from app.reports import generate_borrowing_report_pdf
from app.email_sender import send_borrowing_report

router = APIRouter(prefix="/reports", tags=["reports"])


async def _send_report_task(user_id: int) -> None:
    """Background task: opens its own DB session, generates PDF, sends email."""
    async with SessionLocal() as db:
        # Load user
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if user is None:
            return

        # Load all borrowings for the user with book relationship eagerly loaded
        
        """SELECT borrowings.*, books.*
           FROM borrowings
           LEFT JOIN books ON borrowings.book_id = books.id
           WHERE borrowings.user_id = :user_id
           ORDER BY borrowings.borrowed_at DESC;"""
        
        result = await db.execute(
            select(Borrowing)
            .options(selectinload(Borrowing.book))
            .where(Borrowing.user_id == user_id)
            .order_by(Borrowing.borrowed_at.desc())
        )
        borrowings = result.scalars().all()

        pdf_bytes = generate_borrowing_report_pdf(user, borrowings)
        await send_borrowing_report(user.username, pdf_bytes)


@router.post("/borrowing/{user_id}", status_code=202)
async def send_borrowing_report_email(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """
    Trigger a borrowing report PDF for the given user and email it.
    Accessible by admins and librarians only.
    Returns 202 immediately; the PDF is generated and sent in the background.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UserNotFound()

    background_tasks.add_task(_send_report_task, user_id)

    return {
        "message": f"Report for '{user.username}' is being generated and will be emailed shortly."
    }
