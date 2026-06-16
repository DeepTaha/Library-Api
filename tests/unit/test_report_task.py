"""Unit tests for _send_report_task — the background job in app/routers/reports.py.

The task is called directly (not via HTTP). SessionLocal is patched to the test
DB so no production connection is made. PDF generation and email sending are
mocked to avoid real I/O.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.models.user import User, UserRole
from app.models.book import Book
from app.models.borrowing import Borrowing
from app.security.password import hash_password
from app.routers.reports import _send_report_task



@pytest.mark.asyncio
async def test_generates_pdf_and_sends_email_for_valid_user(
    seeded_reader_with_borrowing, make_session_local_patch
):
    """Happy path — correct user and borrowings passed to the PDF generator and email sender."""
    user_id = seeded_reader_with_borrowing
    mock_pdf = MagicMock(return_value=b"fake-pdf-bytes")
    mock_email = AsyncMock()

    with make_session_local_patch(), \
         patch("app.routers.reports.generate_borrowing_report_pdf", mock_pdf), \
         patch("app.routers.reports.send_borrowing_report", mock_email):
        await _send_report_task(user_id)

    mock_pdf.assert_called_once()
    user_arg, borrowings_arg = mock_pdf.call_args[0]
    assert user_arg.id == user_id
    assert len(borrowings_arg) == 1
    assert borrowings_arg[0].book.title == "1984"
    mock_email.assert_called_once_with("zaid", b"fake-pdf-bytes")


@pytest.mark.asyncio
async def test_generates_pdf_with_empty_borrowings(make_session_local_patch):
    """A user with no borrowings still triggers PDF generation with an empty list."""
    from tests.conftest import _test_session_factory

    async with _test_session_factory() as session:
        user = User(
            username="emptyuser",
            hashed_password=hash_password("pass123456"),
            role=UserRole.READER,
            email="empty@test.com",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        uid = user.id

    mock_pdf = MagicMock(return_value=b"empty-pdf")
    mock_email = AsyncMock()

    with make_session_local_patch(), \
         patch("app.routers.reports.generate_borrowing_report_pdf", mock_pdf), \
         patch("app.routers.reports.send_borrowing_report", mock_email):
        await _send_report_task(uid)

    mock_pdf.assert_called_once()
    _, borrowings_arg = mock_pdf.call_args[0]
    assert borrowings_arg == []
    mock_email.assert_called_once_with("emptyuser", b"empty-pdf")


@pytest.mark.asyncio
async def test_email_failure_propagates(seeded_reader_with_borrowing, make_session_local_patch):
    """An SMTP exception raised by the email sender is not swallowed by the task."""
    mock_pdf = MagicMock(return_value=b"pdf")
    mock_email = AsyncMock(side_effect=RuntimeError("SMTP error"))

    with make_session_local_patch(), \
         patch("app.routers.reports.generate_borrowing_report_pdf", mock_pdf), \
         patch("app.routers.reports.send_borrowing_report", mock_email):
        with pytest.raises(RuntimeError, match="SMTP error"):
            await _send_report_task(seeded_reader_with_borrowing)


@pytest.mark.asyncio
async def test_borrowings_ordered_newest_first(
    seeded_reader_with_borrowing, make_session_local_patch
):
    """Borrowings are passed to the PDF generator ordered by borrowed_at descending."""
    from tests.conftest import _test_session_factory

    user_id = seeded_reader_with_borrowing

    async with _test_session_factory() as session:
        book2 = Book(
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            total_copies=3,
            available_copies=2,
            is_age_restricted=False,
        )
        session.add(book2)
        await session.flush()

        now = datetime.now(timezone.utc)
        older = Borrowing(
            user_id=user_id,
            book_id=book2.id,
            borrowed_at=now - timedelta(days=30),
            due_date=now - timedelta(days=16),
            returned_at=now - timedelta(days=15),
            is_overdue=False,
            extension_count=0,
        )
        session.add(older)
        await session.commit()

    captured = {}

    def capture_pdf(user, borrowings):
        captured["borrowings"] = borrowings
        return b"pdf"

    with make_session_local_patch(), \
         patch("app.routers.reports.generate_borrowing_report_pdf", capture_pdf), \
         patch("app.routers.reports.send_borrowing_report", AsyncMock()):
        await _send_report_task(user_id)

    titles = [b.book.title for b in captured["borrowings"]]
    assert titles[0] == "1984"   # more recent borrowing first
    assert titles[1] == "Dune"
