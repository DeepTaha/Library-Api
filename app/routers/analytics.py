from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas.analytics import AnalyticsSummaryResponse
from app.security import require_librarian
from app.services import LibraryService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """Library usage summary. Librarian/admin only."""
    service = LibraryService(db)
    return await service.get_analytics_summary()
