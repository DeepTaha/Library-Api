from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services import LibraryService
from app.security import require_librarian, require_any_role
from app.models import User
from app import schemas


router = APIRouter(prefix="/books", tags=["books"])


@router.post("/", response_model=schemas.BookResponse, status_code=201)
async def add_book(
    book_data: schemas.BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),   
):
    """Create a new book. Requires librarian or admin role."""
    service = LibraryService(db)
    return await service.add_book(book_data)


@router.get("/", response_model=list[schemas.BookResponse])
async def list_books(
    available: Optional[bool] = None,
    author: Optional[str] = None,
    offset: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role), 
):
    """List books with optional filters. Any logged-in user can view."""
    service = LibraryService(db)
    return await service.get_all_books(available, author, offset, limit)