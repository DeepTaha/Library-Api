import pytest


@pytest.mark.asyncio
async def test_borrowing_decreases_available_copies(client, add_book):
    # Arrange: create a book with 3 copies
    book = await add_book(title="The Hobbit", total=3, available=3)
    
    # Act: borrow it
    response = await client.post("/borrowings/borrow", json={
        "book_id": book["id"],
        "user_name": "alice",
    })
    
    # Assert: the borrow succeeded
    assert response.status_code in (200,201)
    
    # Assert: available_copies dropped from 3 to 2
    book_after = await client.get(f"/books/?author=Test")  # or however you fetch
    # Better: fetch the specific book back
    listing = await client.get("/books/")
    books_now = listing.json()
    assert len(books_now) == 1
    assert books_now[0]["available_copies"] == 2


@pytest.mark.asyncio
async def test_borrowing_with_zero_copies_returns_400(client, add_book):
    # Arrange: create a book with 0 available copies
    book = await add_book(title="Sold Out", total=5, available=0)
    
    # Act: try to borrow it
    response = await client.post("/borrowings/borrow", json={
        "book_id": book["id"],
        "user_name": "alice",
        
    })
    
    # Assert: 400 response
    assert response.status_code == 400
    assert "available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_borrow_same_user_same_book_fails(client, add_book):
    # Arrange: create a book and borrow it once
    book = await add_book(total=5, available=5)
    
    first = await client.post("/borrowings/borrow", json={
        "book_id": book["id"],
        "user_name": "alice",
    })
    assert first.status_code == 200
    
    # Act: try to borrow it again as the same user
    second = await client.post("/borrowings/borrow", json={
        "book_id": book["id"],
        "user_name": "alice",
    })
    
    # Assert: second borrow rejected
    assert second.status_code == 400
    assert "already" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_cannot_borrow_more_than_three_books(client, add_book):
    # Arrange: create 4 different books
    book1 = await add_book(title="Book 1")
    book2 = await add_book(title="Book 2")
    book3 = await add_book(title="Book 3")
    book4 = await add_book(title="Book 4")
    
    # Act: borrow the first three (should all succeed)
    for book in [book1, book2, book3]:
        response = await client.post("/borrowings/borrow", json={
            "book_id": book["id"],
            "user_name": "alice",
        })
        assert response.status_code == 200
    
    # Act: try the fourth
    fourth = await client.post("/borrowings/borrow", json={
        "book_id": book4["id"],
        "user_name": "alice",
    })
    
    # Assert: fourth borrow rejected
    assert fourth.status_code == 400
    assert "maximum" in fourth.json()["detail"].lower() or "3" in fourth.json()["detail"]