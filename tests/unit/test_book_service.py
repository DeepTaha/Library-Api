"""Unit tests for LibraryService book management methods."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.library_service import LibraryService
from app.exceptions import BookNotFound
from app import schemas

# testing the service layer in isolation

def _make_service():
    db = MagicMock()   # creates a fake database session
    db.commit = AsyncMock() 
    db.refresh = AsyncMock()
    service = LibraryService(db) 
    service.book_repo = MagicMock()
    service.borrow_repo = MagicMock()
    return service

# a fake database row
def _fake_book(book_id=1):
    book = MagicMock()
    book.id = book_id
    book.title = "Test Book"
    book.author = "Test Author"
    book.total_copies = 3
    book.available_copies = 3
    book.genre = None
    return book


@pytest.mark.asyncio
async def test_get_book_by_id_raises_not_found():
    service = _make_service()
    service.book_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(BookNotFound):
        await service.get_book_by_id(99)


@pytest.mark.asyncio
async def test_update_book_applies_changes_and_commits():
    service = _make_service()
    book = _fake_book()
    service.book_repo.get_by_id = AsyncMock(return_value=book)

    await service.update_book(1, schemas.BookUpdate(title="New Title", genre="Fiction"))

    assert book.title == "New Title"
    assert book.genre == "Fiction"
    service.db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_book_calls_repo_and_commits():
    service = _make_service()
    book = _fake_book()
    service.book_repo.get_by_id = AsyncMock(return_value=book)
    service.book_repo.delete = AsyncMock()

    await service.delete_book(1)

    service.book_repo.delete.assert_called_once_with(book)
    service.db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_book_borrowings_raises_not_found_for_unknown_book():
    service = _make_service()
    service.book_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(BookNotFound):
        await service.get_book_borrowings(99)
