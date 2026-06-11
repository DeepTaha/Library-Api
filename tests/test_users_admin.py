"""E2E tests for GET/PATCH /users/{id} and POST /users/{id}/reset-password."""
import pytest


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_user_by_id_returns_user(client, admin_headers, seeded_reader):
    # First find the reader's id via list
    listing = await client.get("/users/", headers=admin_headers)
    reader = next(u for u in listing.json() if u["username"] == "testreader")

    response = await client.get(f"/users/{reader['id']}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["username"] == "testreader"


@pytest.mark.asyncio
async def test_get_user_by_id_returns_404_for_unknown(client, admin_headers):
    response = await client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patch_user_changes_role(client, admin_headers, seeded_reader):
    listing = await client.get("/users/", headers=admin_headers)
    reader = next(u for u in listing.json() if u["username"] == "testreader")

    response = await client.patch(
        f"/users/{reader['id']}",
        json={"role": "librarian"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "librarian"


# ---------------------------------------------------------------------------
# POST /users/{id}/reset-password
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_reset_password_allows_login_with_new_password(client, admin_headers, seeded_reader):
    listing = await client.get("/users/", headers=admin_headers)
    reader = next(u for u in listing.json() if u["username"] == "testreader")

    reset = await client.post(
        f"/users/{reader['id']}/reset-password",
        json={"new_password": "brandnewpass99"},
        headers=admin_headers,
    )
    assert reset.status_code == 200

    # Old password no longer works
    old_login = await client.post("/auth/login", data={"username": "testreader", "password": "readerpass123"})
    assert old_login.status_code == 401

    # New password works
    new_login = await client.post("/auth/login", data={"username": "testreader", "password": "brandnewpass99"})
    assert new_login.status_code == 200
