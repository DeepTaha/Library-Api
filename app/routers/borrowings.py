from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import LibraryService
from app.security import require_any_role
from app.models import User
from app import schemas


router = APIRouter(prefix="/borrowings", tags=["borrowings"])


@router.post("/borrow", response_model=schemas.BorrowingResponse, status_code=201)
async def borrow_book(
    request: schemas.BorrowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Borrow a book. The borrowing is tied to the logged-in user."""
    service = LibraryService(db)
    return await service.borrow_book(request, current_user)


@router.post("/return/{borrowing_id}", response_model=schemas.BorrowingResponse)
async def return_book(
    borrowing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Return a borrowed book."""
    service = LibraryService(db)
    return await service.return_book(borrowing_id, current_user)