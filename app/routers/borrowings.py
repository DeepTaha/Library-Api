import csv
import io
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

_CSV_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_csv(value: str) -> str:
    # Prefix with a tab so spreadsheet apps treat the cell as text, not a formula.
    if value and value[0] in _CSV_INJECTION_PREFIXES:
        return "\t" + value
    return value

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, SessionLocal
from app.repositories.borrowing_repository import BorrowingRepository
from app.services import LibraryService
from app.security import require_any_role, require_librarian
from app.models import User
from app import schemas
from app.exceptions import AgeRestricted


router = APIRouter(prefix="/borrowings", tags=["borrowings"])


@router.post("/", response_model=schemas.BorrowingResponse, status_code=201)
async def borrow_book(
    request: schemas.BorrowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    service = LibraryService(db)
    try:
        return await service.borrow_book(request, current_user)
    except AgeRestricted:
        raise HTTPException(status_code=403, detail="This book is restricted to users aged 18 and above.")


# /me and /me/history must be declared before /{id} so FastAPI
# doesn't attempt to coerce "me" into an integer borrowing id.
@router.get(
    "/me",
    response_model=list[schemas.BorrowingResponse],
    summary="Get my active borrowings",
    description=(
        "Returns only **active (unreturned)** borrowings for the logged-in user. "
        "To retrieve completed borrowings use **GET /borrowings/me/history**."
    ),
)
async def get_my_borrowings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    service = LibraryService(db)
    return await service.get_my_borrowings(current_user.id)


@router.get(
    "/me/export",
    responses={200: {"content": {"text/csv": {}}, "description": "CSV file of full borrow history"}},
    response_class=StreamingResponse,
)
async def export_my_borrowings(
    current_user: User = Depends(require_any_role),
):
    """Stream the caller's full borrow history as a CSV file."""
    user_id = current_user.id

    async def csv_rows() -> AsyncGenerator[str, None]:
        buf = io.StringIO()  # a tiny text file that lives in ram
        writer = csv.writer(buf)  # a csv writer that writes on our buffer
        writer.writerow(["title", "author", "borrowed_date", "due_date", "returned_date", "overdue"])
        yield buf.getvalue()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        async with SessionLocal() as db:
            repo = BorrowingRepository(db)
            async for b in repo.stream_history_by_user(user_id):
                if b.returned_at:
                    returned = b.returned_at.replace(tzinfo=None) if b.returned_at.tzinfo else b.returned_at
                    due = b.due_date.replace(tzinfo=None) if b.due_date.tzinfo else b.due_date
                    overdue = "Yes" if returned > due else "No"
                else:
                    overdue = "Yes" if b.due_date < now else "No"

                buf = io.StringIO()
                writer = csv.writer(buf)
                writer.writerow([
                    _safe_csv(b.book.title),
                    _safe_csv(b.book.author),
                    b.borrowed_at.date().isoformat(),
                    b.due_date.date().isoformat(),
                    b.returned_at.date().isoformat() if b.returned_at else "",
                    overdue,
                ])
                yield buf.getvalue()

    return StreamingResponse(
        csv_rows(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=borrow_history.csv"},
    )


@router.get(
    "/me/history",
    response_model=list[schemas.BorrowingResponse],
    summary="Get my borrowing history",
    description=(
        "Returns only **returned (completed)** borrowings for the logged-in user. "
        "To retrieve currently active borrowings use **GET /borrowings/me**."
    ),
)
async def get_my_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    service = LibraryService(db)
    return await service.get_my_history(current_user.id)


@router.get("/", response_model=list[schemas.BorrowingResponse])
async def list_borrowings(
    user_id: Optional[int] = None,
    book_id: Optional[int] = None,
    active: Optional[bool] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """List all borrowings with optional filters. Librarian/admin only."""
    service = LibraryService(db)
    return await service.get_all_borrowings(user_id, book_id, active, offset, limit)


@router.post("/bulk-return", response_model=schemas.BulkReturnResponse)
async def bulk_return(
    request: schemas.BulkReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """Return multiple borrowings in one request. Librarian/admin only.

    Invalid IDs (not found, already returned, wrong reader) are reported in
    the `failed` list — they never block the successful ones from committing.
    """
    service = LibraryService(db)
    return await service.bulk_return(request.borrowing_ids, request.reader_id)


@router.get("/{borrowing_id}", response_model=schemas.BorrowingResponse)
async def get_borrowing(
    borrowing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Get a single borrowing. Librarian/admin can see any; readers see only their own."""
    service = LibraryService(db)
    return await service.get_borrowing_by_id(borrowing_id, current_user)


@router.post("/{borrowing_id}/return", response_model=schemas.BorrowingResponse)
async def return_book(
    borrowing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    service = LibraryService(db)
    return await service.return_book(borrowing_id, current_user)


@router.post("/{borrowing_id}/extend", response_model=schemas.BorrowingResponse)
async def extend_borrowing(
    borrowing_id: int,
    body: schemas.ExtendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """Extend the due date by 1–30 days. Librarian/admin only."""
    service = LibraryService(db)
    return await service.extend_borrowing(borrowing_id, body.days, current_user)
