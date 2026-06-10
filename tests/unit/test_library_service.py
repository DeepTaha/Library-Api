# """Unit tests for LibraryService business rules.

# These tests use mocks instead of a real database — we manually feed the
# service whatever data we want it to see, then check it makes the right decision.
# """
# import pytest
# from unittest.mock import AsyncMock, MagicMock
# from datetime import datetime, timezone

# from app.services.library_service import LibraryService, MAX_ACTIVE_BORROWINGS_PER_USER
# from app.exceptions import (
#     BookNotFound,
#     BookNotAvailable,
#     BorrowLimitExceeded,
#     DuplicateActiveBorrowing,
# )
# from app.models import Book, User, UserRole
# from app import schemas


# def make_service():
#     """Build a LibraryService with mocked dependencies for unit testing."""
#     fake_db = AsyncMock()
#     service = LibraryService(fake_db)
#     # Replace the real repos with mocks we control
#     service.book_repo = AsyncMock()
#     service.borrow_repo = AsyncMock()
#     return service


# def make_user(user_id=1, role=UserRole.READER):
#     """Build a fake User object for tests."""
#     user = MagicMock(spec=User)
#     user.id = user_id
#     user.role = role
#     return user


# def make_book(book_id=1, available_copies=3):
#     """Build a fake Book object for tests."""
#     book = MagicMock(spec=Book)
#     book.id = book_id
#     book.available_copies = available_copies
#     return book


# @pytest.mark.asyncio
# async def test_borrow_raises_when_book_not_found():
#     """If the book doesn't exist, raise BookNotFound."""
#     service = make_service()
#     service.book_repo.get_by_id.return_value = None  # No book found
    
#     user = make_user()
#     request = schemas.BorrowRequest(book_id=999)
    
#     with pytest.raises(BookNotFound):
#         await service.borrow_book(request, user)


# @pytest.mark.asyncio
# async def test_borrow_raises_when_no_copies_available():
#     """If the book has 0 available copies, raise BookNotAvailable."""
#     service = make_service()
#     service.book_repo.get_by_id.return_value = make_book(available_copies=0)
    
#     user = make_user()
#     request = schemas.BorrowRequest(book_id=1)
    
#     with pytest.raises(BookNotAvailable):
#         await service.borrow_book(request, user)


# @pytest.mark.asyncio
# async def test_borrow_raises_when_user_at_borrow_limit():
#     """If user already has the max number of active borrowings, raise BorrowLimitExceeded."""
#     service = make_service()
#     service.book_repo.get_by_id.return_value = make_book(available_copies=3)
#     service.borrow_repo.count_active_by_user.return_value = MAX_ACTIVE_BORROWINGS_PER_USER
    
#     user = make_user()
#     request = schemas.BorrowRequest(book_id=1)
    
#     with pytest.raises(BorrowLimitExceeded):
#         await service.borrow_book(request, user)


# @pytest.mark.asyncio
# async def test_borrow_raises_when_duplicate_active_borrowing():
#     """If user already has an active borrowing for this book, raise DuplicateActiveBorrowing."""
#     service = make_service()
#     service.book_repo.get_by_id.return_value = make_book(available_copies=3)
#     service.borrow_repo.count_active_by_user.return_value = 1
#     # Existing borrowing found
#     service.borrow_repo.find_active_by_user_and_book.return_value = MagicMock()
    
#     user = make_user()
#     request = schemas.BorrowRequest(book_id=1)
    
#     with pytest.raises(DuplicateActiveBorrowing):
#         await service.borrow_book(request, user)


# @pytest.mark.asyncio
# async def test_borrow_succeeds_when_all_checks_pass():
#     """If all rules are satisfied, the borrow should succeed without raising."""
#     service = make_service()
#     book = make_book(available_copies=3)
#     service.book_repo.get_by_id.return_value = book
#     service.borrow_repo.count_active_by_user.return_value = 0
#     service.borrow_repo.find_active_by_user_and_book.return_value = None
#     service.borrow_repo.create.return_value = MagicMock()
    
#     user = make_user()
#     request = schemas.BorrowRequest(book_id=1)
    
#     # Should not raise anything
#     result = await service.borrow_book(request, user)
    
#     # And available_copies should have been decremented
#     assert book.available_copies == 2
    
#     # Verify the repo create was called with the right args
#     service.borrow_repo.create.assert_called_once_with(1, user.id)
    
#     # Verify commit was called
#     service.db.commit.assert_called_once()