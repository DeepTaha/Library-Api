from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.exceptions import (
    BookNotFound,
    BookNotAvailable,
    BorrowingNotFound,
    BorrowLimitExceeded,
    DuplicateActiveBorrowing,
    BookAlreadyReturned,
    InsufficientPermissions,
    AgeRestricted,
    AccountSuspended,
)
from app.repositories.book_repository import BookRepository
from app.repositories.borrowing_repository import BorrowingRepository
from app.repositories.user_repository import UserRepository
from app.models import User, UserRole
from app import schemas

LOG_FILE = Path("overdue.log")
MAX_ACTIVE_BORROWINGS_PER_USER = 3
AGE_RESTRICTION_THRESHOLD = 18


def _user_is_underage(user: User) -> bool:
    """Return True if the user has a DOB and is under 18."""
    if user.date_of_birth is None:
        return False
    today = datetime.now(timezone.utc).date()
    dob = user.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age < AGE_RESTRICTION_THRESHOLD


class LibraryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.book_repo = BookRepository(db)
        self.borrow_repo = BorrowingRepository(db)
        self.user_repo = UserRepository(db)

    async def add_book(self, book_data: schemas.BookCreate):
        book = await self.book_repo.create(book_data.model_dump())
        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def get_all_books(self, available, author, skip: int, limit: int, current_user: User):
        hide_restricted = _user_is_underage(current_user)
        return await self.book_repo.list_all(available, author, skip, limit, hide_restricted)

    async def get_book_by_id(self, book_id: int, current_user: User):
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFound()
        if book.is_age_restricted and _user_is_underage(current_user):
            raise AgeRestricted()
        return book

    async def update_book(self, book_id: int, data: schemas.BookUpdate):
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFound()
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(book, field, value)
        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def delete_book(self, book_id: int):
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFound()
        await self.book_repo.delete(book)
        await self.db.commit()

    async def get_book_borrowings(self, book_id: int):
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFound()
        return await self.borrow_repo.list_by_book(book_id)

    async def find_overdue_borrowings(self):
        return await self.borrow_repo.find_overdue()

    async def get_my_borrowings(self, user_id: int):
        """Active (unreturned) borrowings for the requesting user."""
        return await self.borrow_repo.list_by_user(user_id, returned=False)

    async def get_my_history(self, user_id: int):
        """Returned borrowings for the requesting user."""
        return await self.borrow_repo.list_by_user(user_id, returned=True)

    async def get_all_borrowings(
        self,
        user_id: int | None,
        book_id: int | None,
        active: bool | None,
        offset: int,
        limit: int,
    ):
        return await self.borrow_repo.list_all(user_id, book_id, active, offset, limit)

    async def get_borrowing_by_id(self, borrowing_id: int, current_user: User):
        borrowing = await self.borrow_repo.get_by_id(borrowing_id)
        if borrowing is None:
            raise BorrowingNotFound()
        if (borrowing.user_id != current_user.id
                and current_user.role not in (UserRole.ADMIN, UserRole.LIBRARIAN)):
            raise InsufficientPermissions()
        return borrowing

    async def extend_borrowing(self, borrowing_id: int, days: int, current_user: User):
        borrowing = await self.borrow_repo.get_by_id(borrowing_id)
        if borrowing is None:
            raise BorrowingNotFound()
        if borrowing.returned_at is not None:
            raise BookAlreadyReturned()
        borrowing.due_date = borrowing.due_date + timedelta(days=days)
        await self.db.commit()
        await self.db.refresh(borrowing)
        return borrowing

    async def borrow_book(self, request: schemas.BorrowRequest, current_user: User):
        book = await self.book_repo.get_by_id_locked(request.book_id)

        if not book:
            raise BookNotFound()
        if book.is_age_restricted and _user_is_underage(current_user):
            raise AgeRestricted()
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

        target_user = (
            current_user
            if borrowing.user_id == current_user.id
            else await self.user_repo.get_by_id(borrowing.user_id)
        )
        if target_user and target_user.is_suspended:
            remaining = await self.borrow_repo.count_active_overdue_by_user(target_user.id)
            if remaining == 0:
                target_user.is_suspended = False

        await self.db.commit()
        await self.db.refresh(borrowing)
        return borrowing

    async def bulk_return(
        self,
        borrowing_ids: list[int],
        reader_id: int | None,
    ) -> dict:
        """Process returns for multiple borrowing IDs in one request.

        Each ID is validated independently. All valid returns are committed in
        a single transaction so failures never roll back the successful ones.
        """
        now = datetime.now(timezone.utc)
        succeeded = []
        failed = []

        for bid in borrowing_ids:
            borrowing = await self.borrow_repo.get_by_id(bid)

            if borrowing is None:
                failed.append({"borrowing_id": bid, "reason": "not_found"})
                continue

            if reader_id is not None and borrowing.user_id != reader_id:
                failed.append({"borrowing_id": bid, "reason": "wrong_reader"})
                continue

            if borrowing.returned_at is not None:
                failed.append({"borrowing_id": bid, "reason": "already_returned"})
                continue

            borrowing.returned_at = now
            book = await self.book_repo.get_by_id_locked(borrowing.book_id)
            if book:
                book.available_copies += 1
            succeeded.append(borrowing)

        if succeeded:
            await self.db.commit()
            for b in succeeded:
                await self.db.refresh(b)

            # Lift suspension for users who no longer have any active overdue borrowings.
            seen_users: set[int] = set()
            for b in succeeded:
                if b.user_id not in seen_users:
                    seen_users.add(b.user_id)
                    user = await self.user_repo.get_by_id(b.user_id)
                    if user and user.is_suspended:
                        remaining = await self.borrow_repo.count_active_overdue_by_user(b.user_id)
                        if remaining == 0:
                            user.is_suspended = False
            if seen_users:
                await self.db.commit()

        return {
            "succeeded": succeeded,
            "failed": failed,
            "success_count": len(succeeded),
            "failure_count": len(failed),
        }

    async def get_analytics_summary(self) -> dict:
        return await self.borrow_repo.get_analytics_summary()

    async def process_overdue(self):
        """Mark newly-overdue borrowings in the DB, suspend accounts 7+ days late, and log each one."""
        borrowings = await self.borrow_repo.find_newly_overdue()
        if not borrowings:
            return 0

        now = datetime.now(timezone.utc)
        lines = []
        for borrowing in borrowings:
            borrowing.is_overdue = True
            due_date = borrowing.due_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            days_late = (now - due_date).days
            reader = borrowing.user.username if borrowing.user else f"user#{borrowing.user_id}"
            timestamp = now.strftime("%Y-%m-%d %H:%M")

            if days_late > 7 and borrowing.user and not borrowing.user.is_suspended:
                borrowing.user.is_suspended = True
                lines.append(
                    f'[{timestamp}] SUSPENDED: {reader} — account put on hold '
                    f'({days_late} day(s) overdue on "{borrowing.book.title}")\n'
                )
            else:
                lines.append(
                    f'[{timestamp}] OVERDUE: "{borrowing.book.title}" '
                    f'borrowed by {reader} — {days_late} day(s) late\n'
                )

        await self.db.commit()

        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.writelines(lines)

        return len(borrowings)

    async def log_overdue_borrowings(self, borrowings):
        now = datetime.now(timezone.utc)
        lines = []

        for borrowing in borrowings:
            days_late = (now - borrowing.due_date).days
            reader = borrowing.user.username if borrowing.user else f"user#{borrowing.user_id}"
            timestamp = now.strftime("%Y-%m-%d %H:%M")
            line = (
                f'[{timestamp}] OVERDUE: "{borrowing.book.title}" '
                f'borrowed by {reader} — {days_late} day(s) late\n'
            )
            lines.append(line)

        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.writelines(lines)
