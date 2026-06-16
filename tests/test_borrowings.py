import pytest


@pytest.mark.asyncio
async def test_borrowing_decreases_available_copies(client, admin_headers, reader_headers, add_book):
    book = await add_book(title="The Hobbit", total=3, available=3, headers=admin_headers)

    response = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)
    assert response.status_code in (200, 201)

    listing = await client.get("/books/", headers=reader_headers)
    books_now = listing.json()
    assert len(books_now) == 1
    assert books_now[0]["available_copies"] == 2


@pytest.mark.asyncio
async def test_borrowing_with_zero_copies_returns_400(client, admin_headers, reader_headers, add_book):
    book = await add_book(title="Sold Out", total=5, available=0, headers=admin_headers)

    response = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)

    assert response.status_code == 400
    assert "available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_borrow_same_user_same_book_fails(client, admin_headers, reader_headers, add_book):
    book = await add_book(total=5, available=5, headers=admin_headers)

    first = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)
    assert first.status_code in (200, 201)

    second = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)

    assert second.status_code == 400
    assert "already" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_cannot_borrow_more_than_three_books(client, admin_headers, reader_headers, add_book):
    book1 = await add_book(title="Book 1", headers=admin_headers)
    book2 = await add_book(title="Book 2", headers=admin_headers)
    book3 = await add_book(title="Book 3", headers=admin_headers)
    book4 = await add_book(title="Book 4", headers=admin_headers)

    for book in [book1, book2, book3]:
        response = await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)
        assert response.status_code in (200, 201)

    fourth = await client.post("/borrowings/", json={"book_id": book4["id"]}, headers=reader_headers)

    assert fourth.status_code == 400
    assert "maximum" in fourth.json()["detail"].lower() or "3" in fourth.json()["detail"]
