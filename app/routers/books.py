from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services import LibraryService
from app.security import require_librarian, require_any_role
from app.models import User
from app import schemas
from app.exceptions import AgeRestricted


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
    current_user: User = Depends(require_any_role),  # who can hit on this endpoint(user_dependancy)
):
    """List books with optional filters. Age-restricted books hidden for users under 18."""
    service = LibraryService(db)
    return await service.get_all_books(available, author, offset, limit, current_user)


# /books/{id}/borrowings must be declared before /books/{id}
# so FastAPI doesn't swallow "borrowings" as a book id.
@router.get("/{book_id}/borrowings", response_model=list[schemas.BorrowingResponse])
async def get_book_borrowings(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """Get the full borrow history for a specific book. Librarian/admin only."""
    service = LibraryService(db)
    return await service.get_book_borrowings(book_id)


@router.get("/{book_id}", response_model=schemas.BookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Get a single book by id. Returns 403 for age-restricted books if user is under 18."""
    service = LibraryService(db)
    try:
        return await service.get_book_by_id(book_id, current_user)
    except AgeRestricted:
        raise HTTPException(status_code=403, detail="This book is restricted to users aged 18 and above.")


@router.patch("/{book_id}", response_model=schemas.BookResponse)
async def update_book(
    book_id: int,
    book_data: schemas.BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """Update a book's details or copy counts. Librarian/admin only."""
    service = LibraryService(db)
    return await service.update_book(book_id, book_data)


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """Remove a book entirely. Librarian/admin only."""
    service = LibraryService(db)
    await service.delete_book(book_id)