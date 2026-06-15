from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, SessionLocal
from app.services import LibraryService
from app.security import require_admin
from app.models import User


router = APIRouter(prefix="/admin", tags=["admin"])


async def _log_overdue_task() -> None:
    """Self-contained background task with its own DB session."""
    async with SessionLocal() as db:
        service = LibraryService(db)
        overdue = await service.find_overdue_borrowings()
        await service.log_overdue_borrowings(overdue)


@router.post("/check-overdue")
async def check_overdue(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = LibraryService(db)
    overdue = await service.find_overdue_borrowings()

    background_tasks.add_task(_log_overdue_task)

    return {
        "status": "scheduled",
        "count": len(overdue),
        "message": "Overdue borrowings will be logged in the background"
    }