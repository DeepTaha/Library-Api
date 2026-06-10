from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from pathlib import Path

from app.exceptions import (
    BookNotFound,
    BookNotAvailable,
    BorrowingNotFound,
    BorrowLimitExceeded,
    DuplicateActiveBorrowing,
    BookAlreadyReturned,
    InsufficientPermissions,
)
from app.repositories.book_repository import BookRepository
from app.repositories.borrowing_repository import BorrowingRepository
from app.models import User, UserRole
from app import schemas

LOG_FILE = Path("overdue.log")
MAX_ACTIVE_BORROWINGS_PER_USER = 3


class LibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.book_repo = BookRepository(db)
        self.borrow_repo = BorrowingRepository(db)

    async def add_book(self, book_data: schemas.BookCreate):
        book = await self.book_repo.create(book_data.model_dump())
        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def get_all_books(self, available, author, skip: int, limit: int):
        return await self.book_repo.list_all(available, author, skip, limit)

    async def find_overdue_borrowings(self):
        return await self.borrow_repo.find_overdue()

    async def borrow_book(self, request: schemas.BorrowRequest, current_user: User):
        book = await self.book_repo.get_by_id_locked(request.book_id)

        if not book:
            raise BookNotFound()
        if book.available_copies < 1:
            raise BookNotAvailable()

        active_count = await self.borrow_repo.count_active_by_user(current_user.id)
        if active_count >= MAX_ACTIVE_BORROWINGS_PER_USER:
            raise BorrowLimitExceeded()

        existing = await self.borrow_repo.find_active_by_user_and_book(
            current_user.id, request.book_id
        )
        if existing is not None:
            raise DuplicateActiveBorrowing()

        book.available_copies -= 1
        borrowing = await self.borrow_repo.create(request.book_id, current_user.id)

        await self.db.commit()
        await self.db.refresh(borrowing)
        return borrowing

    async def return_book(self, borrowing_id: int, current_user: User):
        borrowing = await self.borrow_repo.get_by_id(borrowing_id)

        if not borrowing:
            raise BorrowingNotFound()
        if borrowing.returned_at is not None:
            raise BookAlreadyReturned()

        if (borrowing.user_id != current_user.id
                and current_user.role not in (UserRole.ADMIN, UserRole.LIBRARIAN)):
            raise InsufficientPermissions()

        borrowing.returned_at = datetime.now(timezone.utc)
        book = await self.book_repo.get_by_id_locked(borrowing.book_id)
        if book:
            book.available_copies += 1

        await self.db.commit()
        await self.db.refresh(borrowing)
        return borrowing

    async def log_overdue_borrowings(self, borrowings):
        now = datetime.utcnow()
        lines = []

        for borrowing in borrowings:
            days_late = (now - borrowing.due_date).days
            timestamp = now.strftime("%Y-%m-%d %H:%M")
            line = (
                f'[{timestamp}] OVERDUE: "{borrowing.book.title}" '
                f'borrowed by {borrowing.user_id} — {days_late} days late\n'
            )
            lines.append(line)

        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.writelines(lines)
