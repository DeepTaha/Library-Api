"""E2E tests for all /borrowings endpoints."""
import pytest


@pytest.mark.asyncio
async def test_borrow_book_returns_201(client, admin_headers, reader_headers, add_book):
    book = await add_book(total=3, available=3, headers=admin_headers)

    response = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["book_id"] == book["id"]
    assert body["returned_at"] is None
    assert body["due_date"] is not None


@pytest.mark.asyncio
async def test_get_my_borrowings_shows_active_only(client, admin_headers, reader_headers, add_book):
    book1 = await add_book(title="Active Book", total=3, available=3, headers=admin_headers)
    book2 = await add_book(title="Returned Book", total=3, available=3, headers=admin_headers)

    b1 = await client.post("/borrowings/", json={"book_id": book1["id"]}, headers=reader_headers)
    b2 = await client.post("/borrowings/", json={"book_id": book2["id"]}, headers=reader_headers)

    # Return book2
    await client.post(f"/borrowings/{b2.json()['id']}/return", headers=reader_headers)

    response = await client.get("/borrowings/me", headers=reader_headers)
    ids = [b["id"] for b in response.json()]

    assert response.status_code == 200
    assert b1.json()["id"] in ids
    assert b2.json()["id"] not in ids


@pytest.mark.asyncio
async def test_return_moves_to_history(client, admin_headers, reader_headers, add_book):
    book = await add_book(total=3, available=3, headers=admin_headers)
    borrow = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)
    borrowing_id = borrow.json()["id"]

    await client.post(f"/borrowings/{borrowing_id}/return", headers=reader_headers)

    active = await client.get("/borrowings/me", headers=reader_headers)
    history = await client.get("/borrowings/me/history", headers=reader_headers)

    assert all(b["id"] != borrowing_id for b in active.json())
    assert any(b["id"] == borrowing_id for b in history.json())


@pytest.mark.asyncio
async def test_extend_due_date(client, admin_headers, reader_headers, add_book):
    book = await add_book(total=3, available=3, headers=admin_headers)
    borrow = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)
    borrowing_id = borrow.json()["id"]
    original_due = borrow.json()["due_date"]

    response = await client.post(
        f"/borrowings/{borrowing_id}/extend",
        json={"days": 7},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["due_date"] != original_due
