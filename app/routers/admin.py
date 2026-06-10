from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import LibraryService
from app.security import require_admin
from app.models import User


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/check-overdue")
async def check_overdue(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),   
):
    service = LibraryService(db)
    overdue = await service.find_overdue_borrowings()
    
    background_tasks.add_task(service.log_overdue_borrowings, overdue)
    
    return {
        "status": "scheduled",
        "count": len(overdue),
        "message": "Overdue borrowings will be logged in the background"
    }