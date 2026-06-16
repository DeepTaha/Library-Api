"""E2E tests for POST /reports/borrowing/{user_id}.

Hits the real HTTP endpoint via AsyncClient. SessionLocal inside the background
task is patched to the test DB. PDF generation and email sending are mocked
so no real I/O occurs.

With httpx ASGITransport, background tasks run before the response is returned,
so we can assert on their side-effects immediately after the HTTP call.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client, seeded_reader_with_borrowing):
    resp = await client.post(f"/reports/borrowing/{seeded_reader_with_borrowing}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reader_role_returns_403(client, reader_headers, seeded_reader_with_borrowing):
    resp = await client.post(
        f"/reports/borrowing/{seeded_reader_with_borrowing}",
        headers=reader_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unknown_user_id_returns_404(client, librarian_headers, make_session_local_patch):
    with make_session_local_patch(), \
         patch("app.routers.reports.send_borrowing_report", AsyncMock()), \
         patch("app.routers.reports.generate_borrowing_report_pdf", MagicMock(return_value=b"")):
        resp = await client.post("/reports/borrowing/999999", headers=librarian_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_valid_request_returns_202(
    client, librarian_headers, seeded_reader_with_borrowing, make_session_local_patch
):
    with make_session_local_patch(), \
         patch("app.routers.reports.send_borrowing_report", AsyncMock()), \
         patch("app.routers.reports.generate_borrowing_report_pdf", MagicMock(return_value=b"")):
        resp = await client.post(
            f"/reports/borrowing/{seeded_reader_with_borrowing}",
            headers=librarian_headers,
        )
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_response_body_contains_username(
    client, librarian_headers, seeded_reader_with_borrowing, make_session_local_patch
):
    with make_session_local_patch(), \
         patch("app.routers.reports.send_borrowing_report", AsyncMock()), \
         patch("app.routers.reports.generate_borrowing_report_pdf", MagicMock(return_value=b"")):
        resp = await client.post(
            f"/reports/borrowing/{seeded_reader_with_borrowing}",
            headers=librarian_headers,
        )
    assert "zaid" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_background_task_calls_pdf_and_email(
    client, librarian_headers, seeded_reader_with_borrowing, make_session_local_patch
):
    """Both PDF generation and email sending are invoked by the background task."""
    mock_pdf = MagicMock(return_value=b"test-pdf")
    mock_email = AsyncMock()

    with make_session_local_patch(), \
         patch("app.routers.reports.generate_borrowing_report_pdf", mock_pdf), \
         patch("app.routers.reports.send_borrowing_report", mock_email):
        resp = await client.post(
            f"/reports/borrowing/{seeded_reader_with_borrowing}",
            headers=librarian_headers,
        )

    assert resp.status_code == 202
    mock_pdf.assert_called_once()
    mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_background_task_receives_correct_user_and_borrowings(
    client, librarian_headers, seeded_reader_with_borrowing, make_session_local_patch
):
    """The user and borrowings forwarded to the PDF generator match the requested user."""
    captured = {}

    def capture(user, borrowings):
        captured["user"] = user
        captured["borrowings"] = borrowings
        return b"pdf"

    with make_session_local_patch(), \
         patch("app.routers.reports.generate_borrowing_report_pdf", capture), \
         patch("app.routers.reports.send_borrowing_report", AsyncMock()):
        await client.post(
            f"/reports/borrowing/{seeded_reader_with_borrowing}",
            headers=librarian_headers,
        )

    assert captured["user"].id == seeded_reader_with_borrowing
    assert captured["user"].username == "zaid"
    assert len(captured["borrowings"]) == 1
    assert captured["borrowings"][0].book.title == "1984"


@pytest.mark.asyncio
async def test_admin_can_also_trigger_report(
    client, admin_headers, seeded_reader_with_borrowing, make_session_local_patch
):
    """Admins have librarian-or-above access and can trigger reports."""
    with make_session_local_patch(), \
         patch("app.routers.reports.send_borrowing_report", AsyncMock()), \
         patch("app.routers.reports.generate_borrowing_report_pdf", MagicMock(return_value=b"")):
        resp = await client.post(
            f"/reports/borrowing/{seeded_reader_with_borrowing}",
            headers=admin_headers,
        )
    assert resp.status_code == 202
