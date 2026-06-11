"""E2E tests for GET/PATCH/DELETE /books/{id} and GET /books/{id}/borrowings."""
import pytest


@pytest.mark.asyncio
async def test_get_book_by_id_returns_book(client, admin_headers, add_book):
    book = await add_book(title="Dune", headers=admin_headers)

    response = await client.get(f"/books/{book['id']}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["title"] == "Dune"


@pytest.mark.asyncio
async def test_patch_book_updates_fields(client, admin_headers, add_book):
    book = await add_book(headers=admin_headers)

    response = await client.patch(
        f"/books/{book['id']}",
        json={"title": "Updated Title", "genre": "Sci-Fi"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated Title"
    assert body["genre"] == "Sci-Fi"


@pytest.mark.asyncio
async def test_delete_book_returns_204_and_book_gone(client, admin_headers, add_book):
    book = await add_book(headers=admin_headers)

    delete_resp = await client.delete(f"/books/{book['id']}", headers=admin_headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/books/{book['id']}", headers=admin_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_book_borrowings_returns_borrow_history(client, admin_headers, seeded_reader, reader_headers, add_book):
    book = await add_book(total=5, available=5, headers=admin_headers)

    # Reader borrows the book
    await client.post("/borrowings/", json={"book_id": book["id"]}, headers=reader_headers)

    response = await client.get(f"/books/{book['id']}/borrowings", headers=admin_headers)

    assert response.status_code == 200
    borrowings = response.json()
    assert len(borrowings) == 1
    assert borrowings[0]["book_id"] == book["id"]
