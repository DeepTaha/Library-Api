"""E2E tests for POST /auth/logout."""
import pytest


@pytest.mark.asyncio
async def test_logout_returns_200_with_message(client, reader_headers):
    response = await client.post("/auth/logout", headers=reader_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}


@pytest.mark.asyncio
async def test_logout_invalidates_token(client, reader_headers):
    await client.post("/auth/logout", headers=reader_headers)
    after = await client.get("/users/me", headers=reader_headers)
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_logout_without_token_returns_401(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_new_login_after_logout_issues_fresh_token(client, seeded_reader, reader_headers):
    await client.post("/auth/logout", headers=reader_headers)

    login_resp = await client.post("/auth/login", data=seeded_reader)
    new_token = login_resp.json()["access_token"]

    profile = await client.get("/users/me", headers={"Authorization": f"Bearer {new_token}"})
    assert profile.status_code == 200
