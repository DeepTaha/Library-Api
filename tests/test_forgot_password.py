"""E2E tests for POST /auth/forgot-password."""
import pytest


@pytest.mark.asyncio
async def test_registered_email_returns_200_with_token(client, seeded_reader):
    response = await client.post("/auth/forgot-password", json={"email": "testreader@test.com"})

    assert response.status_code == 200
    body = response.json()
    assert "reset link" in body["message"].lower()
    assert body["reset_token"] is not None


@pytest.mark.asyncio
async def test_unknown_email_returns_200_same_message(client):
    response = await client.post("/auth/forgot-password", json={"email": "nobody@test.com"})

    assert response.status_code == 200
    body = response.json()
    assert "reset link" in body["message"].lower()
    assert body["reset_token"] is None  # no token — but same message as valid email


@pytest.mark.asyncio
async def test_missing_email_field_returns_422(client):
    response = await client.post("/auth/forgot-password", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_token_is_stored_and_linked_to_user(client, seeded_reader):
    from app.security import reset_tokens

    response = await client.post("/auth/forgot-password", json={"email": "testreader@test.com"})
    token = response.json()["reset_token"]

    # Token resolves back to a user id — proving the store was populated
    user_id = reset_tokens.get_user_id(token)
    assert user_id is not None
    assert isinstance(user_id, int)
