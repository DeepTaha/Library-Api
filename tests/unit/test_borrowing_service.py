"""Unit tests for LibraryService borrowing management methods."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from app.services.library_service import LibraryService
from app.exceptions import BorrowingNotFound, BookAlreadyReturned, InsufficientPermissions
from app.models.user import UserRole


def _make_service():
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    service = LibraryService(db)
    service.book_repo = MagicMock()
    service.borrow_repo = MagicMock()
    return service


def _fake_user(user_id=1, role=UserRole.READER):
    user = MagicMock()
    user.id = user_id
    user.role = role
    return user


def _fake_borrowing(borrowing_id=1, user_id=1, returned=False):
    b = MagicMock()
    b.id = borrowing_id
    b.user_id = user_id
    b.due_date = datetime.now(timezone.utc) + timedelta(days=7)
    b.returned_at = datetime.now(timezone.utc) if returned else None
    return b


@pytest.mark.asyncio
async def test_get_my_borrowings_queries_active_only():
    service = _make_service()
    service.borrow_repo.list_by_user = AsyncMock(return_value=[])

    await service.get_my_borrowings(user_id=5)

    service.borrow_repo.list_by_user.assert_called_once_with(5, returned=False)


@pytest.mark.asyncio
async def test_extend_borrowing_adds_days():
    service = _make_service()
    borrowing = _fake_borrowing()
    original_due = borrowing.due_date
    service.borrow_repo.get_by_id = AsyncMock(return_value=borrowing)

    await service.extend_borrowing(borrowing_id=1, days=7, current_user=_fake_user())

    assert borrowing.due_date == original_due + timedelta(days=7)
    service.db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_extend_already_returned_raises():
    service = _make_service()
    service.borrow_repo.get_by_id = AsyncMock(return_value=_fake_borrowing(returned=True))

    with pytest.raises(BookAlreadyReturned):
        await service.extend_borrowing(1, days=5, current_user=_fake_user())


@pytest.mark.asyncio
async def test_get_borrowing_by_id_raises_for_non_owner():
    service = _make_service()
    # Borrowing belongs to user 1, requesting user is 2 with READER role
    service.borrow_repo.get_by_id = AsyncMock(return_value=_fake_borrowing(user_id=1))
    non_owner = _fake_user(user_id=2, role=UserRole.READER)

    with pytest.raises(InsufficientPermissions):
        await service.get_borrowing_by_id(1, non_owner)
